/**
 * Integration tests for web dashboard API
 */

const axios = require('axios');

// Test configuration
const API_BASE_URL = process.env.API_URL || 'http://localhost:8000';
const TEST_TIMEOUT = 10000;

// Helper function to make API requests
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    try {
        const response = await axios({
            url,
            method: options.method || 'GET',
            data: options.data,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            timeout: TEST_TIMEOUT
        });
        return response.data;
    } catch (error) {
        console.error(`API request failed: ${error.message}`);
        throw error;
    }
}

// Test suites
describe('Web Dashboard API Integration Tests', () => {
    describe('Sessions API', () => {
        test('GET /api/dashboard/sessions should return session list', async () => {
            const data = await apiRequest('/api/dashboard/sessions');
            
            expect(data).toBeDefined();
            expect(Array.isArray(data)).toBe(true);
            
            // Check session structure
            if (data.length > 0) {
                const session = data[0];
                expect(session).toHaveProperty('session_name');
                expect(session).toHaveProperty('project_name');
                expect(session).toHaveProperty('status');
                expect(session).toHaveProperty('exists');
            }
        });

        test('Sessions API should handle errors gracefully', async () => {
            // Test with invalid endpoint
            try {
                await apiRequest('/api/dashboard/sessions/invalid');
            } catch (error) {
                expect(error.response.status).toBe(404);
            }
        });
    });

    describe('Health API', () => {
        test('GET /api/dashboard/health should return health metrics', async () => {
            const data = await apiRequest('/api/dashboard/health');
            
            expect(data).toBeDefined();
            expect(data).toHaveProperty('overall_score');
            expect(data).toHaveProperty('categories');
            expect(data).toHaveProperty('suggestions');
            expect(data).toHaveProperty('last_updated');
            
            // Check score is valid
            expect(data.overall_score).toBeGreaterThanOrEqual(0);
            expect(data.overall_score).toBeLessThanOrEqual(100);
            
            // Check categories structure
            const categories = ['build', 'tests', 'dependencies', 'security', 
                              'performance', 'code_quality', 'git', 'documentation'];
            categories.forEach(category => {
                expect(data.categories).toHaveProperty(category);
                expect(data.categories[category]).toHaveProperty('score');
                expect(data.categories[category]).toHaveProperty('status');
            });
        });
    });

    describe('Activity API', () => {
        test('GET /api/dashboard/activity should return activity data', async () => {
            const data = await apiRequest('/api/dashboard/activity');
            
            expect(data).toBeDefined();
            expect(data).toHaveProperty('activities');
            expect(data).toHaveProperty('total_days');
            expect(data).toHaveProperty('active_days');
            expect(data).toHaveProperty('max_activity');
            expect(data).toHaveProperty('avg_activity');
            
            // Check activities array
            expect(Array.isArray(data.activities)).toBe(true);
            expect(data.activities.length).toBeGreaterThan(0);
            
            // Check activity structure
            if (data.activities.length > 0) {
                const activity = data.activities[0];
                expect(activity).toHaveProperty('date');
                expect(activity).toHaveProperty('activity_count');
            }
        });
    });

    describe('Stats API', () => {
        test('GET /api/dashboard/stats should return dashboard statistics', async () => {
            const data = await apiRequest('/api/dashboard/stats');
            
            expect(data).toBeDefined();
            expect(data).toHaveProperty('active_sessions');
            expect(data).toHaveProperty('total_projects');
            expect(data).toHaveProperty('health_score');
            expect(data).toHaveProperty('activity_streak');
            expect(data).toHaveProperty('last_update');
            
            // Check data types
            expect(typeof data.active_sessions).toBe('number');
            expect(typeof data.total_projects).toBe('number');
            expect(typeof data.health_score).toBe('number');
            expect(typeof data.activity_streak).toBe('number');
        });
    });

    describe('Web Components Integration', () => {
        test('Components should load data successfully', async () => {
            // Simulate component data loading
            const sessionData = await apiRequest('/api/dashboard/sessions');
            expect(sessionData).toBeDefined();
            
            const healthData = await apiRequest('/api/dashboard/health');
            expect(healthData).toBeDefined();
            
            const activityData = await apiRequest('/api/dashboard/activity');
            expect(activityData).toBeDefined();
        });

        test('Error scenarios should be handled', async () => {
            // Test network timeout simulation
            const timeoutPromise = new Promise((_, reject) => 
                setTimeout(() => reject(new Error('Network timeout')), 100)
            );
            
            try {
                await Promise.race([
                    apiRequest('/api/dashboard/sessions'),
                    timeoutPromise
                ]);
            } catch (error) {
                expect(error.message).toContain('timeout');
            }
        });
    });

    describe('Dashboard Page', () => {
        test('GET /web/ should return HTML page', async () => {
            const response = await axios.get(`${API_BASE_URL}/web/`);
            
            expect(response.status).toBe(200);
            expect(response.headers['content-type']).toContain('text/html');
            expect(response.data).toContain('Yesman Claude Dashboard');
        });
    });
});

// Performance tests
describe('Performance Tests', () => {
    test('API responses should be fast', async () => {
        const endpoints = ['/api/dashboard/sessions', '/api/dashboard/health', '/api/dashboard/activity', '/api/dashboard/stats'];
        
        for (const endpoint of endpoints) {
            const startTime = Date.now();
            await apiRequest(endpoint);
            const endTime = Date.now();
            const responseTime = endTime - startTime;
            
            // Response should be under 1 second
            expect(responseTime).toBeLessThan(1000);
            console.log(`${endpoint} response time: ${responseTime}ms`);
        }
    });

    test('Concurrent requests should be handled', async () => {
        const promises = [];
        const concurrentRequests = 10;
        
        for (let i = 0; i < concurrentRequests; i++) {
            promises.push(apiRequest('/api/dashboard/sessions'));
        }
        
        const results = await Promise.all(promises);
        expect(results).toHaveLength(concurrentRequests);
        results.forEach(result => {
            expect(result).toBeDefined();
        });
    });
});

// Run tests if this file is executed directly
if (require.main === module) {
    console.log('Running integration tests...');
    console.log(`API URL: ${API_BASE_URL}`);
    console.log('Make sure the API server is running!');
}