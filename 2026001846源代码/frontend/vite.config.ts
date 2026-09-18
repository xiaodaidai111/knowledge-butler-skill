import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { existsSync, statSync, createReadStream } from 'node:fs'
import { resolve, extname, join, relative, isAbsolute } from 'node:path'
import { fileURLToPath } from 'node:url'

const staticRoot = resolve(fileURLToPath(import.meta.url), '..', 'static')
const mimeTypes: Record<string, string> = {
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.webp': 'image/webp',
  '.ico': 'image/x-icon',
  '.css': 'text/css',
  '.js': 'application/javascript',
  '.json': 'application/json',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
}

const serveStaticPlugin = () => ({
  name: 'serve-static',
  configureServer(server: any) {
    server.middlewares.use((req: any, res: any, next: any) => {
      const url = req.url || ''
      if (!url.startsWith('/static/') && url !== '/static') return next()
      // URL 路径必须按 POSIX 语义切分。原来用 normalize() 再判断 includes('\\')，
      // 而 Windows 的 normalize() 会把 / 全部转成 \，于是每个子目录请求
      // （/static/agents/x.png、/static/icons/y.png）都被判成越权返回 403。
      const segments = decodeURIComponent(url.replace(/^\/static\/?/, ''))
        .split(/[\\/]+/)
        .filter((segment) => segment !== '' && segment !== '.')
      if (segments.length === 0 || segments.some((segment) => segment === '..' || segment.includes(':'))) {
        res.statusCode = 403
        res.end('Forbidden')
        return
      }
      const filePath = join(staticRoot, ...segments)
      const escaped = relative(staticRoot, filePath)
      if (escaped.startsWith('..') || isAbsolute(escaped) || !existsSync(filePath) || !statSync(filePath).isFile()) {
        res.statusCode = 404
        res.end('Not Found')
        return
      }
      res.setHeader('Content-Type', mimeTypes[extname(filePath).toLowerCase()] || 'application/octet-stream')
      res.setHeader('Cache-Control', 'no-cache')
      try {
        createReadStream(filePath).pipe(res)
      } catch (e) {
        res.statusCode = 500
        res.end('Internal Server Error')
      }
    })
  },
})

export default defineConfig({
  plugins: [vue(), serveStaticPlugin()],
  publicDir: false,
  // 编辑器原子保存时会把 @vitejs/plugin-vue 当成新依赖去预构建，esbuild 会因为
  // 它导出名是 "module.exports" 直接报错并把优化流程打断；插件本身不需要预构建。
  optimizeDeps: {
    exclude: ['@vitejs/plugin-vue']
  },
  server: {
    host: '127.0.0.1',
    port: 5173,
    watch: {
      // 编辑器原子写会在项目目录里留下 .App.vue.<pid>.tmpdir/ 这类临时目录，
      // Windows 上 watcher 撞到被占用的临时文件会抛 EBUSY 并终止整个 dev server，
      // 所以显式忽略它们。
      ignored: ['**/.*.tmpdir/**', '**/*.tmpdir/**', '**/*.tmp']
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('/node_modules/zrender/')) return 'zrender'
          if (id.includes('/node_modules/echarts/')) return 'echarts'
        }
      }
    }
  }
})
