use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CacheEntry<T> {
    pub data: T,
    pub created_at: DateTime<Utc>,
    pub expires_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Serialize)]
pub struct CacheStats {
    pub total_entries: usize,
    pub hits: u64,
    pub misses: u64,
    pub evictions: u64,
    pub hit_rate: f64,
    pub memory_size_bytes: usize,
}

pub struct Cache<T> {
    data: Arc<RwLock<HashMap<String, CacheEntry<T>>>>,
    hits: Arc<RwLock<u64>>,
    misses: Arc<RwLock<u64>>,
    evictions: Arc<RwLock<u64>>,
    max_entries: usize,
    default_ttl_seconds: u64,
}

impl<T: Clone + Send + Sync + 'static> Cache<T> {
    pub fn new(max_entries: usize, default_ttl_seconds: u64) -> Self {
        Self {
            data: Arc::new(RwLock::new(HashMap::new())),
            hits: Arc::new(RwLock::new(0)),
            misses: Arc::new(RwLock::new(0)),
            evictions: Arc::new(RwLock::new(0)),
            max_entries,
            default_ttl_seconds,
        }
    }
    
    pub async fn get(&self, key: &str) -> Option<T> {
        let data = self.data.read().await;
        
        if let Some(entry) = data.get(key) {
            // 만료 확인
            if let Some(expires_at) = entry.expires_at {
                if Utc::now() > expires_at {
                    drop(data);
                    self.remove(key).await;
                    *self.misses.write().await += 1;
                    return None;
                }
            }
            
            *self.hits.write().await += 1;
            Some(entry.data.clone())
        } else {
            *self.misses.write().await += 1;
            None
        }
    }
    
    pub async fn set(&self, key: String, value: T) {
        self.set_with_ttl(key, value, None).await;
    }
    
    pub async fn set_with_ttl(&self, key: String, value: T, ttl_seconds: Option<u64>) {
        let mut data = self.data.write().await;
        
        // 크기 제한 확인
        if data.len() >= self.max_entries && !data.contains_key(&key) {
            // 가장 오래된 항목 제거 (LRU 스타일)
            if let Some((oldest_key, _)) = data.iter()
                .min_by_key(|(_, entry)| entry.created_at)
                .map(|(k, v)| (k.clone(), v.clone())) {
                data.remove(&oldest_key);
                *self.evictions.write().await += 1;
            }
        }
        
        let ttl = ttl_seconds.unwrap_or(self.default_ttl_seconds);
        let expires_at = if ttl > 0 {
            Some(Utc::now() + chrono::Duration::seconds(ttl as i64))
        } else {
            None
        };
        
        let entry = CacheEntry {
            data: value,
            created_at: Utc::now(),
            expires_at,
        };
        
        data.insert(key, entry);
    }
    
    pub async fn remove(&self, key: &str) -> Option<T> {
        let mut data = self.data.write().await;
        data.remove(key).map(|entry| entry.data)
    }
    
    pub async fn clear(&self) {
        let mut data = self.data.write().await;
        data.clear();
    }
    
    pub async fn cleanup_expired(&self) {
        let mut data = self.data.write().await;
        let now = Utc::now();
        let mut expired_keys = Vec::new();
        
        for (key, entry) in data.iter() {
            if let Some(expires_at) = entry.expires_at {
                if now > expires_at {
                    expired_keys.push(key.clone());
                }
            }
        }
        
        for key in expired_keys {
            data.remove(&key);
            *self.evictions.write().await += 1;
        }
    }
    
    pub async fn get_stats(&self) -> CacheStats {
        let data = self.data.read().await;
        let hits = *self.hits.read().await;
        let misses = *self.misses.read().await;
        let evictions = *self.evictions.read().await;
        
        let total_requests = hits + misses;
        let hit_rate = if total_requests > 0 {
            (hits as f64 / total_requests as f64) * 100.0
        } else {
            0.0
        };
        
        // 대략적인 메모리 사용량 계산 (실제로는 더 정확한 계산 필요)
        let memory_size_bytes = data.len() * std::mem::size_of::<CacheEntry<T>>();
        
        CacheStats {
            total_entries: data.len(),
            hits,
            misses,
            evictions,
            hit_rate,
            memory_size_bytes,
        }
    }
}

// 전역 캐시 인스턴스들
lazy_static::lazy_static! {
    pub static ref SESSION_CACHE: Cache<String> = Cache::new(100, 300); // 5분 TTL
    pub static ref CONFIG_CACHE: Cache<String> = Cache::new(50, 3600);  // 1시간 TTL
}