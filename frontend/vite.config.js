import path from 'node:path';
import react from '@vitejs/plugin-react';
import { defineConfig, loadEnv } from 'vite';
export default defineConfig(function (_a) {
    var mode = _a.mode;
    var env = loadEnv(mode, process.cwd(), '');
    var buildId = env.VITE_APP_BUILD_ID || new Date().toISOString();
    return {
        plugins: [
            react(),
            {
                name: 'emit-build-meta',
                generateBundle: function () {
                    this.emitFile({
                        type: 'asset',
                        fileName: 'build-meta.json',
                        source: JSON.stringify({ buildId: buildId }, null, 2),
                    });
                },
            },
        ],
        build: {
            emptyOutDir: true,
            rollupOptions: {
                output: {
                    manualChunks: {
                        react: ['react', 'react-dom', 'react-router-dom'],
                        antd: ['antd', '@ant-design/icons'],
                        charts: ['echarts', 'echarts-for-react'],
                        network: ['axios'],
                    },
                },
            },
        },
        resolve: {
            alias: {
                '@': path.resolve(__dirname, './src'),
            },
        },
        define: {
            __APP_BUILD_ID__: JSON.stringify(buildId),
        },
        server: {
            host: env.VITE_DEV_HOST || '127.0.0.1',
            port: Number(env.VITE_DEV_PORT || 5173),
        },
    };
});
