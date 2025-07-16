import devtoolsJson from 'vite-plugin-devtools-json';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig(({ mode }) => ({
	plugins: [
		sveltekit(),
		// DevTools integration only in development
		mode === 'development' && devtoolsJson()
	].filter(Boolean),
	// Tauri expects a fixed port
	server: {
		port: 5173,
		strictPort: true,
		host: "localhost",
		// Proxy API requests to the backend server
		proxy: {
			'/api': {
				target: 'http://localhost:8080',
				changeOrigin: true
			}
		}
	},
	// Prevent vite from obscuring rust errors
	clearScreen: false,
	// Tauri uses environment variables that start with TAURI_
	envPrefix: ['VITE_', 'TAURI_'],
	build: {
		// Tauri uses Chromium on Windows and WebKit on macOS and Linux
		target: process.env.TAURI_PLATFORM == 'windows' ? 'chrome105' : 'safari13',
		// don't minify for debug builds
		minify: !process.env.TAURI_DEBUG ? 'esbuild' : false,
		// produce sourcemaps for debug builds
		sourcemap: !!process.env.TAURI_DEBUG
	}
}));
