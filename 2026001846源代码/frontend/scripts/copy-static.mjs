import { copyFileSync, existsSync, mkdirSync, readdirSync, rmSync, statSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const source = resolve(root, 'static')
const target = resolve(root, 'dist/static')

const copyDir = (from, to) => {
  mkdirSync(to, { recursive: true })
  let count = 0
  for (const entry of readdirSync(from, { withFileTypes: true })) {
    const sourcePath = resolve(from, entry.name)
    const targetPath = resolve(to, entry.name)
    if (entry.isDirectory()) {
      count += copyDir(sourcePath, targetPath)
    } else if (entry.isFile()) {
      copyFileSync(sourcePath, targetPath)
      count += 1
    }
  }
  return count
}

if (existsSync(source) && statSync(source).isDirectory()) {
  rmSync(target, { recursive: true, force: true })
  const count = copyDir(source, target)
  console.log(`static assets copied to dist/static (${count} files)`)
}
