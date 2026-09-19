import { chromium } from 'playwright'
import fs from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const baseURL = process.env.UI_BASE_URL || 'http://127.0.0.1:5174/'
const outputDir = fileURLToPath(new URL('./ui-visual-results/', import.meta.url))
const pages = [
  ['home', '首页'],
  ['context', '智能检索'],
  ['tasks', '检修任务'],
  ['skills', '知识库'],
  ['profile', '个人中心']
]
const viewports = [
  ['desktop', { width: 1920, height: 1080 }],
  ['wide-laptop', { width: 1600, height: 900 }],
  ['compact-laptop', { width: 1440, height: 900 }],
  ['laptop', { width: 1366, height: 768 }]
]

await fs.mkdir(outputDir, { recursive: true })
const browser = await chromium.launch({ channel: 'msedge', headless: true })
const report = []

for (const [viewportName, viewport] of viewports) {
  const context = await browser.newContext({ viewport })
  await context.addInitScript(() => {
    localStorage.setItem('yixiu-web-session', JSON.stringify({ account: 'yixiu', loginAt: Date.now() }))
    sessionStorage.setItem('yixiu-splash-seen', '1')
  })
  const page = await context.newPage()
  await page.goto(baseURL, { waitUntil: 'networkidle' })
  await page.waitForTimeout(800)

  for (const [key, label] of pages) {
    const navButton = page.locator('.side-nav nav button').filter({ hasText: label }).first()
    await navButton.click()
    await page.waitForTimeout(500)
    const metrics = await page.evaluate(() => ({
      viewportWidth: document.documentElement.clientWidth,
      documentWidth: document.documentElement.scrollWidth,
      bodyWidth: document.body.scrollWidth,
      horizontalOverflow: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - document.documentElement.clientWidth,
      visibleOverflows: [...document.querySelectorAll('body *')]
        .filter((el) => {
          const style = getComputedStyle(el)
          const rect = el.getBoundingClientRect()
          return rect.width > 0 && rect.right > document.documentElement.clientWidth + 1 && style.position !== 'fixed'
        })
        .slice(0, 8)
        .map((el) => ({ className: el.className?.toString().slice(0, 100), right: Math.round(el.getBoundingClientRect().right) }))
    }))
    report.push({ viewport: viewportName, page: key, ...metrics })
    await page.screenshot({ path: path.join(outputDir, `${viewportName}-${key}.png`), fullPage: false })
  }
  await context.close()
}

await browser.close()
await fs.writeFile(path.join(outputDir, 'report.json'), JSON.stringify(report, null, 2))
console.log(JSON.stringify(report, null, 2))
