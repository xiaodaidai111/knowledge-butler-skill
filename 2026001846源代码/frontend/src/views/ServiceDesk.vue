<template>
  <div class="service-desk" :class="{ 'sd-chat-mode': panel === 'diagnose' && mode === 'freeform' }">
    <header class="sd-hero">
      <div>
        <p class="sd-eyebrow">Service Desk</p>
        <h2>服务台</h2>
        <p class="sd-sub">需求体检 → 开通托管 → 周期交付，把一次性任务变成长周期服务</p>
      </div>
      <div class="sd-tabs">
        <button type="button" :class="{ active: panel === 'diagnose' }" @click="panel = 'diagnose'">需求体检</button>
        <button type="button" :class="{ active: panel === 'learn' }" @click="panel = 'learn'">提示词库</button>
        <button type="button" :class="{ active: panel === 'hosting' }" @click="panel = 'hosting'">
          托管运行<em v-if="kpi.warnings">{{ kpi.warnings }}</em>
        </button>
      </div>
    </header>

    <!-- 体检模式切换：引导问卷精度更高，自由描述更省事 -->
    <div v-if="panel === 'diagnose'" class="sd-modes">
      <button type="button" :class="{ active: mode === 'guided' }" @click="mode = 'guided'">
        <b>分步引导</b>
        <small>5 步问清频次与数据源，给出可行性评分与 ROI</small>
      </button>
      <button type="button" :class="{ active: mode === 'freeform' }" @click="mode = 'freeform'">
        <b>自由描述</b>
        <small>直接说你在忙什么，按关键词估算</small>
      </button>
    </div>

    <!-- ===================== 需求体检 · 分步引导 ===================== -->
    <section v-if="panel === 'diagnose' && mode === 'guided'" class="sd-guided">
      <div class="sd-guide-hero">
        <div>
          <b>用 5 个问题，算出这件事值不值得交给 Agent</b>
          <small>频次 × 耗时 × 规则化程度 × 数据可得性 → 可行性评分、净收益与回本周期</small>
        </div>
      </div>

      <div class="sd-howto">
        <span v-for="(h, i) in HOW_TO" :key="h.t">
          <em>{{ i + 1 }}</em>
          <b>{{ h.t }}</b>
          <small>{{ h.d }}</small>
        </span>
      </div>

      <div class="sd-steps">
        <span v-for="(s, i) in STEPS" :key="s.key" :class="{ on: i === step, done: i < step }">
          <em>{{ i + 1 }}</em><small>{{ s.label }}</small>
        </span>
      </div>

      <div v-if="!report" class="sd-form">
        <div class="sd-form-head">
          <span class="sd-step-no" aria-hidden="true">{{ step + 1 }}</span>
          <div class="sd-form-headcopy">
            <h3>{{ STEPS[step].title }}</h3>
            <p class="sd-hint">{{ STEPS[step].hint }}</p>
            <p class="sd-why"><b>为什么问这个</b>{{ STEPS[step].why }}</p>
          </div>
        </div>
        <p v-if="!optionsLoading && !options.roles.length" class="sd-hint sd-hint-warn">
          体检选项未加载。若后端刚更新过代码，请重启后端再刷新本页。
        </p>

        <div v-if="STEPS[step].key === 'role'" class="sd-chips">
          <button v-for="r in options.roles" :key="r" type="button"
                  :class="{ on: intake.role === r }" @click="intake.role = r">{{ r }}</button>
        </div>

        <div v-else-if="STEPS[step].key === 'tasks'" class="sd-chips wide">
          <button v-for="t in options.tasks" :key="t.task" type="button"
                  :class="{ on: intake.tasks.includes(t.task) }" @click="toggleIn(intake.tasks, t.task)">
            {{ t.task }}<em>{{ t.position }}</em>
          </button>
        </div>

        <div v-else-if="STEPS[step].key === 'frequency'" class="sd-chips">
          <button v-for="f in options.frequency" :key="f.key" type="button"
                  :class="{ on: intake.frequency === f.key }" @click="intake.frequency = f.key">{{ f.label }}</button>
        </div>

        <div v-else-if="STEPS[step].key === 'duration'" class="sd-chips">
          <button v-for="d in options.duration" :key="d.key" type="button"
                  :class="{ on: intake.duration === d.key }" @click="intake.duration = d.key">{{ d.label }}</button>
        </div>

        <div v-else class="sd-chips wide">
          <button v-for="s in options.dataSources" :key="s.key" type="button"
                  :class="{ on: intake.sources.includes(s.key) }" @click="toggleIn(intake.sources, s.key)">
            {{ s.label }}
          </button>
          <label class="sd-note">补充说明（可选）
            <input v-model="intake.note" placeholder="例如：现在用飞书表格手工汇总，每周还要发给 3 个同事复核" />
          </label>
        </div>

        <div class="sd-form-foot">
          <button v-if="step > 0" type="button" @click="step--">上一步</button>
          <span class="sd-progress">{{ step + 1 }} / {{ STEPS.length }}</span>
          <button v-if="step < STEPS.length - 1" class="primary" type="button"
                  :disabled="!canNext" @click="step++">下一步</button>
          <button v-else class="primary" type="button" :disabled="busy || !canNext" @click="submitIntake">
            {{ busy ? '体检中…' : '生成体检报告' }}
          </button>
        </div>
      </div>

      <div v-else class="sd-report">
        <div class="sd-verdict" :class="verdictTone">
          <div>
            <p class="sd-eyebrow">体检结论</p>
            <h3>{{ report.verdict }}</h3>
            <p>{{ report.advice }}</p>
          </div>
          <button type="button" @click="resetIntake">重新体检</button>
        </div>

        <div v-if="report.details && report.details.length" class="sd-report-grid">
          <article v-for="(d, i) in report.details" :key="d.position" class="sd-report-card" :class="{ top: i === 0 }">
            <header>
              <div>
                <b>{{ d.position }}</b>
                <small>{{ d.task }}</small>
              </div>
              <span class="sd-ring" :style="ringStyle(d.feasibility)">
                <em>{{ d.feasibility }}</em><small>可行性</small>
              </span>
            </header>

            <div class="sd-dims">
              <span v-for="dim in DIMS" :key="dim.key">
                <small>{{ dim.label }}</small>
                <i><b :style="{ width: (d.dimensions[dim.key] || 0) + '%' }"></b></i>
                <em>{{ d.dimensions[dim.key] }}</em>
              </span>
            </div>

            <div class="sd-roi">
              <span><small>每周省</small><b>{{ d.automation.savedHoursPerWeek }}h</b></span>
              <span><small>月节省</small><b>¥{{ d.automation.monthlySaving }}</b></span>
              <span><small>托管费</small><b>¥{{ d.automation.monthlyCost }}</b></span>
              <span :class="{ neg: d.automation.netBenefit <= 0 }">
                <small>净收益</small><b>¥{{ d.automation.netBenefit }}</b>
              </span>
              <span><small>回本</small><b>{{ d.automation.paybackDays }} 天</b></span>
            </div>

            <details>
              <summary>落地路径（3 周）</summary>
              <ol class="sd-plan">
                <li v-for="w in d.rollout" :key="w.week">
                  <b>{{ w.week }} · {{ w.title }}</b>
                  <ul><li v-for="it in w.items" :key="it">{{ it }}</li></ul>
                </li>
              </ol>
            </details>

            <details>
              <summary>前置条件（{{ d.prerequisites.filter((p) => p.ready).length }}/{{ d.prerequisites.length }} 已具备）</summary>
              <ul class="sd-prereq">
                <li v-for="p in d.prerequisites" :key="p.item" :class="{ miss: !p.ready }">
                  <b>{{ p.item }}</b><small>{{ p.note }}</small>
                </li>
              </ul>
            </details>

            <details>
              <summary>验收标准</summary>
              <ul class="sd-accept"><li v-for="a in (report.positions[i] || {}).acceptance || []" :key="a">{{ a }}</li></ul>
            </details>

            <div class="sd-report-actions">
              <button class="primary" type="button" :disabled="busy" @click="openHosting({ position: report.positions[i], tasks: report.tasks })">
                开通托管
              </button>
              <button type="button" @click="copyReport(d)">复制这项方案</button>
            </div>
          </article>
        </div>

        <ul class="sd-risks"><li v-for="r in report.risks" :key="r">{{ r }}</li></ul>
      </div>
    </section>

    <!-- ===================== 需求体检 · 自由描述 ===================== -->
    <section v-else-if="panel === 'diagnose'" class="sd-chat">
      <header class="sd-chat-head">
        <img class="sd-ava big" :src="AVATAR" alt="观微" />
        <div>
          <b>观微｜需求诊断师</b>
          <small>说清你每天重复在做的事，我来判断哪些可以交给 Agent</small>
        </div>
        <div class="sd-tools">
          <small>可对接</small>
          <span v-for="t in tools" :key="t.name" class="sd-tool" :title="t.name">
            <img :src="t.logo" :alt="t.name" loading="lazy" />
          </span>
        </div>
      </header>

      <div class="sd-facts">
        <small>已了解</small>
        <span :class="{ on: chatProfile.task }">重复事项</span>
        <span :class="{ on: chatProfile.frequency }">频次</span>
        <span :class="{ on: chatProfile.duration }">耗时</span>
        <span :class="{ on: chatProfile.sources.length }">数据源</span>
        <em v-if="chatProfile.task">{{ chatProfile.task }}</em>
      </div>

      <div ref="threadRef" class="sd-thread">
        <div v-for="(m, i) in messages" :key="i" :class="['sd-msg', m.role]">
          <img v-if="m.role === 'assistant'" class="sd-ava" :src="AVATAR" alt="观微" />
          <div class="sd-bubble">
            <p>{{ m.text }}</p>

            <div v-if="m.chips && m.chips.length && i === messages.length - 1" class="sd-replies">
              <button v-for="c in m.chips" :key="c" type="button" :disabled="busy" @click="send(c)">{{ c }}</button>
            </div>

            <div v-if="m.card" class="sd-diag">
              <ul class="sd-diag-tasks">
                <li v-for="t in m.card.tasks" :key="t.title">
                  <span>{{ t.title }}</span>
                  <em :class="t.priority === '高' ? 'high' : 'mid'">{{ t.priority }}</em>
                </li>
              </ul>
              <div v-if="m.card.position" class="sd-diag-meta">
                <span><small>推荐岗位</small><b>{{ m.card.position.position }}</b></span>
                <span><small>参考价</small><b>{{ m.card.position.price }}</b></span>
                <span><small>运行周期</small><b>{{ m.card.position.cycle }}</b></span>
                <span><small>预计节省</small><b>{{ m.card.savingHours }}h/周</b></span>
              </div>
              <div class="sd-diag-actions">
                <button class="primary" type="button" :disabled="busy" @click="openHosting(m.card)">开通托管</button>
                <button type="button" @click="copyPlan(m.card)">复制方案</button>
              </div>
            </div>
          </div>
        </div>
        <div v-if="busy" class="sd-msg assistant">
          <img class="sd-ava" :src="AVATAR" alt="" />
          <div class="sd-bubble"><p class="typing">正在抽取任务与岗位…</p></div>
        </div>
      </div>


      <form class="sd-input" @submit.prevent="send()">
        <input v-model="draft" placeholder="例如：我每天要手动看同行价格，还要整理客户咨询…" />
        <button type="submit" :disabled="busy || !draft.trim()">{{ busy ? '诊断中' : '发送' }}</button>
      </form>
    </section>

    <!-- ===================== 托管运行 ===================== -->
    <div v-else-if="panel === 'hosting'" class="sd-hosting">
      <div class="sd-kpis">
        <span><b>{{ kpi.hosting }}</b><small>托管中</small></span>
        <span><b>{{ kpi.runs }}</b><small>累计运行</small></span>
        <span><b>{{ kpi.successRate }}%</b><small>成功率</small></span>
        <span><b>¥{{ kpi.cost }}</b><small>累计成本</small></span>
        <span :class="{ warn: kpi.warnings > 0 }"><b>{{ kpi.warnings }}</b><small>待处理异常</small></span>
        <button type="button" class="sd-kpi-btn" @click="showCreate = !showCreate">
          {{ showCreate ? '收起' : '+ 新建托管' }}
        </button>
      </div>

      <!-- 把体检结论带进托管面板：原来「体检 → 开通托管」之后就断在这里，
           看不到当初算出来的收益，也没法对照。 -->
      <div v-if="report && report.ready" class="sd-host-brief">
        <div class="sd-host-brief-copy">
          <p class="sd-eyebrow">体检结论</p>
          <h3>{{ report.verdict }}</h3>
          <small>{{ report.advice }}</small>
        </div>
        <div class="sd-host-brief-metrics">
          <span><small>每周可省</small><b>{{ report.savingHours }}h</b></span>
          <span><small>每月节省</small><b>¥{{ topAutomation.monthlySaving || 0 }}</b></span>
          <span><small>托管费</small><b>¥{{ topAutomation.monthlyCost || 0 }}</b></span>
          <span :class="{ neg: (topAutomation.netBenefit || 0) <= 0 }">
            <small>净收益</small><b>¥{{ topAutomation.netBenefit || 0 }}</b>
          </span>
          <span><small>回本</small><b>{{ topAutomation.paybackDays || '—' }} 天</b></span>
        </div>
        <button type="button" @click="panel = 'diagnose'">重新体检</button>
      </div>

      <form v-if="showCreate" class="sd-create" @submit.prevent="createHosting()">
        <label>服务名称<input v-model="createForm.name" placeholder="如：竞品价格周报" /></label>
        <label>套餐
          <select v-model="createForm.plan">
            <option>基础版</option><option>专业版</option><option>企业版</option>
          </select>
        </label>
        <label>运行周期<input v-model="createForm.cycle" placeholder="如：每周一 09:00" /></label>
        <label>参考价<input v-model="createForm.price" placeholder="如：¥499/月" /></label>
        <button class="primary" type="submit" :disabled="busy || !createForm.name.trim()">开通</button>
      </form>

      <div class="sd-host-grid">
        <section class="sd-card sd-host-list">
          <header><b>托管服务</b><small>{{ hostings.length }} 个</small></header>

          <article v-for="h in hostings" :key="h.id" class="sd-host" :class="{ open: expanded === h.id }">
            <div class="sd-host-head" @click="expanded = expanded === h.id ? '' : h.id">
              <span class="sd-host-mark" :class="`tone-${hostTone(h.name)}`" aria-hidden="true">{{ hostMark(h.name) }}</span>
              <div class="sd-host-info">
                <b>{{ h.name }}</b>
                <small>{{ h.plan }} · {{ h.cycle }}</small>
                <div class="sd-quota"><i :style="{ width: quotaWidth(h) }" :class="{ full: h.usedRuns >= h.quotaRuns }"></i></div>
                <small class="sd-quota-text">本月 {{ h.usedRuns }}/{{ h.quotaRuns }} 次 · 成功率 {{ h.successRate }}%</small>
              </div>
              <div class="sd-host-right">
                <em :class="{ paused: h.status === 'paused' }">{{ h.status === 'paused' ? '已暂停' : '运行中' }}</em>
                <small>下次 {{ h.nextRunAt }}</small>
                <small>{{ relativeDays(h.nextRunAt) }}</small>
              </div>
            </div>

            <div v-if="expanded === h.id" class="sd-runs">
              <div class="sd-run-actions">
                <button type="button" class="primary" :disabled="busy" @click="runNow(h)">
                  {{ busy ? '运行中…' : '立即运行一次' }}
                </button>
                <button type="button" :disabled="busy" @click="toggleStatus(h)">
                  {{ h.status === 'paused' ? '恢复运行' : '暂停服务' }}
                </button>
                <small>运行产物自动归档，可在下方记录中查看</small>
              </div>
              <table v-if="h.runs.length">
                <thead><tr><th>运行时间</th><th>状态</th><th>耗时</th><th>成本</th><th>产物</th></tr></thead>
                <tbody>
                  <tr v-for="r in h.runs" :key="r.id">
                    <td>{{ r.startedAt }}</td>
                    <td><em :class="r.status">{{ r.status === 'success' ? '成功' : '告警' }}</em></td>
                    <td>{{ r.duration }}</td>
                    <td>¥{{ r.cost }}</td>
                    <td>
                      <span v-for="a in r.artifacts" :key="a" class="sd-artifact">
                        <i :class="artifactKind(a)">{{ artifactExt(a) }}</i>{{ a }}
                      </span>
                      <small v-if="r.note" class="sd-note">{{ r.note }}</small>
                    </td>
                  </tr>
                </tbody>
              </table>
              <p v-else class="sd-empty small">尚无运行记录，点击「立即运行一次」试试</p>
            </div>
          </article>

          <div v-if="!hostings.length" class="sd-empty">
            <p>还没有托管服务</p>
            <button type="button" @click="panel = 'diagnose'">去做需求体检</button>
          </div>
        </section>

        <section class="sd-card sd-board">
          <header><b>运行看板</b></header>

          <div class="sd-board-block">
            <h4>成功率趋势</h4>
            <div class="sd-bars">
              <span v-for="(v, i) in trend" :key="i" :class="{ low: v < 90 }">
                <i :style="{ height: v + '%' }"></i>
              </span>
            </div>
            <div class="sd-bar-axis">
              <em v-for="(v, i) in trend" :key="i" :class="{ low: v < 90 }">{{ v }}%</em>
            </div>
            <small class="sd-axis">最近 {{ trend.length }} 次运行</small>
          </div>

          <div class="sd-board-block">
            <h4>待处理异常</h4>
            <p v-if="!warningList.length" class="sd-empty small">暂无异常</p>
            <div v-for="w in warningList" :key="w.id" class="sd-warn">
              <b>⚠</b>
              <div>
                <span>{{ w.text }}</span>
                <button type="button" @click="gotoHosting(w.hostingId)">查看</button>
              </div>
            </div>
          </div>

          <div class="sd-board-block">
            <h4>验收证据链（Eval）</h4>
            <ul class="sd-evi-list">
              <li><b>✓</b>规则校验通过 <em>{{ kpi.runs }} 次</em></li>
              <li><b>✓</b>产物已归档，可回溯原始记录</li>
              <li><b>✓</b>人工复核记录可追溯</li>
            </ul>
          </div>
        </section>
      </div>
    </div>

    <!-- ===================== 教程 · 应用 ===================== -->
    <div v-else-if="panel === 'learn'" class="sd-learn">
      <section class="sd-learn-block">
        <header>
          <p class="sd-eyebrow">提示词</p>
          <h3>常用提示词，复制即用</h3>
          <small>把提示词发给 Codex / Claude Code，或直接拿去填体检问卷。也可以存下你自己的常用说法。</small>
          <button class="primary" type="button" @click="showPromptForm = !showPromptForm">
            {{ showPromptForm ? '收起' : '＋ 保存我的提示词' }}
          </button>
        </header>

        <div class="sd-prompt-filter">
          <button
            v-for="g in promptGroupList"
            :key="g"
            type="button"
            :class="{ on: promptGroup === g }"
            @click="promptGroup = g"
          >{{ g }}<em v-if="g !== '全部'">{{ promptCountIn(g) }}</em></button>
        </div>

        <form v-if="showPromptForm" class="sd-prompt-form" @submit.prevent="savePrompt()">
          <label>名称<input v-model.trim="promptForm.title" placeholder="如：每周竞品巡店" /></label>
          <label class="wide">提示词内容<textarea v-model.trim="promptForm.text" placeholder="写下你平时怎么交代这件事，如：每周一帮我把主要竞品的价格和活动抓一遍…"></textarea></label>
          <div class="sd-prompt-form-foot">
            <small>保存在本机浏览器，随时可删</small>
            <button class="primary" type="submit" :disabled="!promptForm.title || !promptForm.text">保存</button>
          </div>
        </form>

        <div class="sd-prompt-grid">
          <article v-for="p in visiblePrompts" :key="p.name" class="sd-prompt" :class="{ custom: p.custom }">
            <header>
              <b>{{ p.name }}</b>
              <em v-if="p.custom">我的</em>
              <em v-else-if="p.optimized" class="sd-prompt-optimized">已优化</em>
              <em v-else-if="p.group" class="sd-prompt-group">{{ p.group }}</em>
            </header>
            <p class="sd-prompt-desc">{{ p.desc }}</p>
            <code class="sd-prompt-text">{{ p.prompt }}</code>
            <div class="sd-prompt-actions">
              <button class="primary" type="button" @click="copyPromptText(p)">复制提示词</button>
              <button type="button" class="optimize" @click="openOptimize(p)">优化</button>
              <button v-if="p.optimized" type="button" @click="resetOptimize(p)">恢复默认</button>
              <button v-if="p.custom" type="button" class="danger" @click="deletePrompt(p)">删除</button>
            </div>
          </article>
        </div>
      </section>
    </div>

    
    <!-- 提示放在组件根级：引导 / 托管 / 教程三个面板都能看到反馈 -->
    <p v-if="toast" class="sd-toast">{{ toast }}</p>
      <!-- 提示词优化弹窗 -->
    <div v-if="optimizeTarget" class="sd-modal" @click.self="optimizeTarget = null">
      <div class="sd-modal-box">
        <header>
          <div>
            <p class="sd-eyebrow">优化提示词</p>
            <b>{{ optimizeTarget.name }}</b>
            <small>{{ optimizeTarget.desc }}</small>
          </div>
          <button class="sd-modal-close" type="button" @click="optimizeTarget = null" aria-label="关闭">✕</button>
        </header>
        <textarea v-model="optimizeText" placeholder="在原提示词基础上补充你的业务细节，例如公司名、固定口径、必须遵守的约束…"></textarea>
        <div class="sd-modal-foot">
          <small>{{ optimizeText.length }} 字 · 保存后这张卡片就用你的版本</small>
          <div>
            <button type="button" @click="optimizeText = optimizeTarget.prompt">还原</button>
            <button type="button" @click="optimizeTarget = null">取消</button>
            <button class="primary" type="button" :disabled="!optimizeText.trim()" @click="saveOptimize">保存</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { yixiuApi } from '../api/yixiuWeb.js'

const props = defineProps({
  account: { type: String, default: '' },
  initialPanel: { type: String, default: 'diagnose' },
  // 由父组件下发，复用上下文中心同一份一键导入提示词，避免两处漂移
  importPrompt: { type: String, default: '' },
  // Skill 推荐榜数据来自工作台那份 skillRankList（含实时仓库信号），这里只做展示
  skills: { type: Array, default: () => [] }
})

const emit = defineEmits(['open-skills'])

const panel = ref(props.initialPanel === 'hosting' ? 'hosting' : 'diagnose')
const draft = ref('')
const busy = ref(false)
const toast = ref('')
const expanded = ref('')
const showCreate = ref(false)
const threadRef = ref(null)

const hostings = ref([])
const kpi = ref({ hosting: 0, runs: 0, successRate: 100, cost: 0, warnings: 0 })
const createForm = reactive({ name: '', plan: '基础版', cycle: '每周一 09:00', price: '¥499/月' })

const AVATAR = '/static/service-desk/avatar-guanwei.png'
// 必须用变量绑定（:src）而不是字面量 src="/static/..."：字面量会被 Vite 当成资源导入，
// 自动请求 /static/...?import 拿到 404，进而让整个 SFC 模块加载失败。

const tools = [
  { name: 'Codex', logo: '/static/agent-logos/codex.svg' },
  { name: 'Claude Code', logo: '/static/agent-logos/claude-code.png' },
  { name: 'Cursor', logo: '/static/agent-logos/cursor.png' },
  { name: '通义千问', logo: '/static/agent-logos/qwen.png' },
  { name: 'DeepSeek', logo: '/static/agent-logos/deepseek.svg' }
]



const messages = ref([
  {
    role: 'assistant',
    text: '我是观微，需求诊断师。说说你每天或每周反复在做、又很占时间的事，我来判断哪些可以交给 Agent。'
  }
])

// 服务首字图标：确定性地按名称取字与配色，不用重复的占位图
const HOST_TONES = ['teal', 'blue', 'amber', 'violet', 'green', 'coral']
const hostMark = (name) => String(name || '?').replace(/^AI\s*/i, '').trim().slice(0, 1) || '·'
const hostTone = (name) => HOST_TONES[[...String(name || '')].reduce((sum, ch) => sum + ch.charCodeAt(0), 0) % HOST_TONES.length]


const artifactExt = (name) => {
  const m = String(name || '').match(/\.([a-z0-9]+)$/i)
  return m ? m[1].toUpperCase() : 'FILE'
}

const artifactKind = (name) => {
  const e = artifactExt(name).toLowerCase()
  if (e === 'xlsx' || e === 'xls' || e === 'csv') return 'xls'
  if (e === 'pdf') return 'pdf'
  if (e === 'md' || e === 'txt') return 'txt'
  return 'file'
}

const relativeDays = (text) => {
  const m = String(text || '').match(/(\d{2})-(\d{2})\s+(\d{2}):(\d{2})/)
  if (!m) return ''
  const now = new Date()
  let target = new Date(now.getFullYear(), Number(m[1]) - 1, Number(m[2]), Number(m[3]), Number(m[4]))
  if (target < now) target = new Date(target.getTime() + 365 * 86400000)
  const days = Math.round((target - now) / 86400000)
  if (days <= 0) return '今天'
  if (days === 1) return '明天'
  return `${days} 天后`
}

const trend = computed(() => {
  const all = []
  hostings.value.forEach((h) => h.runs.forEach((r) => all.push(r)))
  all.sort((a, b) => String(a.startedAt).localeCompare(String(b.startedAt)))
  const tail = all.slice(-10)
  if (!tail.length) return [100]
  return tail.map((r) => (r.status === 'success' ? 100 : 72))
})

const warningList = computed(() => {
  const out = []
  hostings.value.forEach((h) => {
    if (h.usedRuns >= h.quotaRuns) {
      out.push({ id: h.id + '-q', hostingId: h.id, text: `${h.name}：本月运行额度已用尽（${h.usedRuns}/${h.quotaRuns}）` })
    }
    h.runs.filter((r) => r.status !== 'success').forEach((r) => {
      out.push({ id: r.id, hostingId: h.id, text: `${h.name}：${r.startedAt} ${r.note || '本次运行告警'}` })
    })
  })
  return out
})

const quotaWidth = (h) => `${Math.min(100, Math.round(((h.usedRuns || 0) / (h.quotaRuns || 1)) * 100))}%`

const flash = (text) => {
  toast.value = text
  window.setTimeout(() => { if (toast.value === text) toast.value = '' }, 3200)
}

const scrollThread = async () => {
  await nextTick()
  if (threadRef.value) threadRef.value.scrollTop = threadRef.value.scrollHeight
}

// ---- 多轮问答：先问清频次 / 耗时 / 数据源，再给建议与方案 ----
const chatStage = ref('')
const chatProfile = reactive({ task: '', frequency: '', duration: '', sources: [] })

const matchOption = (text, list, extra = []) => {
  const t = String(text || '')
  const hit = list.find((o) => t.includes(o.label))
  if (hit) return hit.key
  for (const rule of extra) {
    if (rule.re.test(t)) return rule.key
  }
  return ''
}

const FREQ_RULES = [
  { key: 'daily_multi', re: /每天\s*(好几|几|多)次|一天\s*(好几|几)次|多次/ },
  { key: 'daily', re: /每天|每日|天天/ },
  { key: 'weekly_multi', re: /每周\s*(好几|几)次|一周\s*(好几|几)次/ },
  { key: 'weekly', re: /每周|每星期|一周一次/ },
  { key: 'monthly', re: /每月|每个月/ }
]
const DURATION_RULES = [
  { key: 't15', re: /15\s*分钟|十几分钟|十分钟|几分钟/ },
  { key: 't120', re: /1\s*小时以上|一个多小时|两三个小时|半天/ },
  { key: 't60', re: /半小时|30\s*分钟|一小时|1\s*小时/ },
  { key: 't30', re: /20\s*分钟|一二十分钟/ }
]

const applyAnswer = (text) => {
  const stage = chatStage.value
  const t = String(text || '')
  if (stage === 'frequency') {
    chatProfile.frequency = matchOption(t, options.value.frequency, FREQ_RULES) || chatProfile.frequency
  } else if (stage === 'duration') {
    chatProfile.duration = matchOption(t, options.value.duration, DURATION_RULES) || chatProfile.duration
  } else if (stage === 'sources') {
    options.value.dataSources.forEach((o) => {
      if (t.includes(o.label) && !chatProfile.sources.includes(o.key)) chatProfile.sources.push(o.key)
    })
  }
  chatStage.value = ''
}

const nextQuestion = () => {
  const freq = options.value.frequency
  const dur = options.value.duration
  const src = options.value.dataSources
  if (!chatProfile.frequency && freq.length) {
    return { key: 'frequency', text: '这件事多久做一次？频次直接决定自动化值不值得做。',
             chips: freq.map((f) => f.label) }
  }
  if (!chatProfile.duration && dur.length) {
    return { key: 'duration', text: '每次大概要花多久？频次乘上耗时，就是每周真正被占掉的工时。',
             chips: dur.map((d) => d.label) }
  }
  if (!chatProfile.sources.length && src.length) {
    return { key: 'sources', text: '需要读取哪些数据？可多选 —— 缺数据源是托管失败最常见的原因。',
             chips: src.map((x) => x.label) }
  }
  return null
}

const resetChat = () => {
  chatStage.value = ''
  chatProfile.task = ''
  chatProfile.frequency = ''
  chatProfile.duration = ''
  chatProfile.sources = []
}

const send = async (text) => {
  const content = String(text || draft.value || '').trim()
  if (!content || busy.value) return
  messages.value.push({ role: 'user', text: content })
  draft.value = ''
  busy.value = true
  await scrollThread()
  try {
    applyAnswer(content)

    // 第一轮先记下「重复事项」；后续每轮记录一个字段
    if (!chatProfile.task) chatProfile.task = content

    const pending = nextQuestion()
    const userTurns = messages.value.filter((m) => m.role === 'user').length
    if (pending && userTurns < 4) {
      chatStage.value = pending.key
      messages.value.push({ role: 'assistant', text: pending.text, chips: pending.chips })
      return
    }

    const data = await yixiuApi.serviceDiagnose({
      account: props.account,
      messages: messages.value,
      intake: {
        ...intake,
        tasks: chatProfile.task ? [chatProfile.task] : intake.tasks,
        frequency: chatProfile.frequency || intake.frequency,
        duration: chatProfile.duration || intake.duration,
        sources: chatProfile.sources.length ? chatProfile.sources : intake.sources
      }
    })
    const report = data.report || {}
    if (report.ready) {
      const top = (report.positions || [])[0] || null
      const verdict = report.verdict || ''
      const head = verdict.includes('不托管')
        ? `先说结论：${verdict}。${report.advice || ''}`
        : `我的建议是：${verdict}。${report.advice || ''}`
      messages.value.push({
        role: 'assistant',
        text: `${head} 下面是按可行性排出来的方案，你可以先看再决定。`,
        card: { tasks: report.tasks, position: top, savingHours: report.savingHours, priceRange: report.priceRange }
      })
    } else {
      messages.value.push({ role: 'assistant', text: '这轮信息还不够，请再补充一句：你反复在做的是什么？大概多久一次？' })
    }
  } catch (error) {
    flash('诊断服务不可用，请确认后端已启动')
  } finally {
    busy.value = false
    await scrollThread()
  }
}

const copyPlan = async (card) => {
  const lines = [
    `可自动化任务（共 ${card.tasks.length} 项）`,
    ...card.tasks.map((t) => `· ${t.title}（优先级 ${t.priority}）`)
  ]
  if (card.position) {
    lines.push('', `推荐岗位：${card.position.position}`)
    lines.push(`交付内容：${card.position.deliverable}`)
    lines.push(`参考价：${card.position.price}｜周期：${card.position.cycle}`)
    lines.push(`验收标准：${(card.position.acceptance || []).join('；')}`)
  }
  lines.push(`预计每周节省：${card.savingHours} 小时`)
  try {
    await navigator.clipboard.writeText(lines.join('\n'))
    flash('方案已复制到剪贴板')
  } catch (e) {
    flash('浏览器未授权剪贴板，请手动复制')
  }
}

const openHosting = async (card) => {
  const top = card.position || {}
  busy.value = true
  try {
    await yixiuApi.createHosting({
      account: props.account,
      name: top.position || '定制 Agent 托管',
      plan: '专业版',
      cycle: top.cycle || '每周一 09:00',
      price: top.price || '¥999/月'
    })
    panel.value = 'hosting'
    await loadHostings()
    flash(`已开通托管：${top.position || '定制 Agent'}`)
  } catch (error) {
    flash('开通托管失败')
  } finally {
    busy.value = false
  }
}

const createHosting = async () => {
  if (!createForm.name.trim()) return
  busy.value = true
  try {
    await yixiuApi.createHosting({ account: props.account, ...createForm })
    createForm.name = ''
    showCreate.value = false
    await loadHostings()
    flash('已开通托管')
  } catch (error) {
    flash('开通托管失败')
  } finally {
    busy.value = false
  }
}

const toggleStatus = async (h) => {
  const next = h.status === 'paused' ? 'running' : 'paused'
  busy.value = true
  try {
    await yixiuApi.setHostingStatus(h.id, next)
    await loadHostings()
    flash(next === 'paused' ? '已暂停服务' : '已恢复运行')
  } catch (error) {
    flash('操作失败')
  } finally {
    busy.value = false
  }
}

const runNow = async (h) => {
  busy.value = true
  try {
    await yixiuApi.runHosting(h.id)
    await loadHostings()
    expanded.value = h.id
    flash(`${h.name} 本次运行完成`)
  } catch (error) {
    flash('运行失败')
  } finally {
    busy.value = false
  }
}

const gotoHosting = (id) => {
  expanded.value = id
  nextTick(() => {
    const el = document.querySelector('.sd-host.open')
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  })
}

const loadHostings = async () => {
  try {
    const data = await yixiuApi.hostings(props.account)
    hostings.value = data.items || []
    kpi.value = data.kpi || kpi.value
    if (!expanded.value && hostings.value.length) expanded.value = hostings.value[0].id
  } catch (error) {
    flash('托管数据加载失败')
  }
}

// ---- 需求体检：分步引导 ----
// 设计意图：自由描述只能靠关键词猜频次与耗时，误差大；引导问卷用用户填的真实值
// 替换基线参数，可行性评分与 ROI 才站得住。两种模式并存，默认走引导。
const mode = ref('guided')
const step = ref(0)
const report = ref(null)
const options = ref({ roles: [], dataSources: [], frequency: [], duration: [], tasks: [], hourlyRate: 80 })
const optionsLoading = ref(true)
const intake = reactive({ role: '', tasks: [], frequency: '', duration: '', sources: [], note: '' })

const STEPS = [
  { key: 'role', label: '角色', title: '你在团队里主要负责什么？',
    hint: '决定推荐岗位的优先级，可随时返回修改。',
    why: '岗位决定了哪些活值得自动化：运营偏数据与监控、销售偏线索与跟进、客服偏咨询整理。先知道你是谁，推荐才不会跑偏。' },
  { key: 'tasks', label: '重复事项', title: '哪些事你每天或每周反复在做？',
    hint: '可多选。选得越准，岗位匹配越准。',
    why: '同一个岗位做的事差别很大。勾到具体事项，才能匹配到对的 Agent 岗位，而不是笼统丢一句「帮你提效」。' },
  { key: 'frequency', label: '频次', title: '这类事多久做一次？',
    hint: '频次直接决定自动化收益的高低。',
    why: '频次是收益的上限：每天一次和每月一次，同样的活自动化价值差几十倍。这一步决定值不值得做。' },
  { key: 'duration', label: '耗时', title: '每次大概要花多久？',
    hint: '频次 × 单次耗时 = 每周被占用的工时。',
    why: '频次乘上单次耗时，就是每周真正被占掉的工时 —— 这是算 ROI 和回本周期的分母。' },
  { key: 'sources', label: '数据来源', title: '需要读取哪些数据？',
    hint: '决定可行性评分中的「数据可得性」维度。',
    why: '数据拿不拿得到，决定这件事到底做不做得成。拿不到就只是纸面方案，所以这一项会直接影响可行性评分。' }
]

const DIMS = [
  { key: 'frequency', label: '频次' },
  { key: 'regularity', label: '规则化程度' },
  { key: 'data', label: '数据可得性' },
  { key: 'timeCost', label: '单次耗时' }
]

// 服务台首页只展示前 5 条，完整榜单在能力中心 · Skill 工厂
const topSkills = computed(() => (props.skills || []).slice(0, 5))

// 体检报告里首选方案的收益数据，带到托管面板顶部做对照
const topAutomation = computed(() => (report.value?.details?.[0]?.automation) || {})

// ---- 需求体检：用法说明、常见场景、评分口径、常见问题 ----
const HOW_TO = [
  { t: '选岗位', d: '先说清你在团队里主要负责任么' },
  { t: '说重复事项', d: '勾出每天或每周重复在做的事' },
  { t: '拿体检报告', d: '得到可行性评分、净收益与落地路径' }
]




// ---- 教程 · 应用 ----

// 提示词模板：可直接复制发送，也可一键填好体检问卷
const PROMPTS = [
  { name: '竞品价格周报', task: '竞品价格与活动监控', role: '运营', frequency: 'weekly', duration: 't30',
    sources: ['web', 'sheet'], group: '市场运营', desc: '每周抓取同行价格与活动变化，产出变化表、周报与异常提醒。',
    prompt: '每周一上午，帮我把 3~5 家主要竞品的官网、店铺价格和活动抓一遍，整理成对比表。价格波动超过 5%、或者出现新的促销活动时单独标出来提醒我，最后输出一份可以直接转发的周报。' },
  { name: '客户咨询整理', task: '客户咨询与聊天记录整理', role: '客服', frequency: 'daily', duration: 't30',
    sources: ['chat', 'sheet'], group: '客户服务', desc: '每日汇总聊天记录，分类客户问题并生成待跟进清单。',
    prompt: '每天下班前，把今天的客户咨询和聊天记录汇总一遍，按问题类型分类，统计每类出现多少次，并列出还需要我跟进的人和事。涉及客户隐私的信息请先脱敏。' },
  { name: '经营日报生成', task: '经营数据汇总与日报生成', role: '运营', frequency: 'daily', duration: 't60',
    sources: ['sheet', 'api'], group: '数据分析', desc: '每日汇总多源数据，产出经营日报、缺失字段标注与异常提示。',
    prompt: '每天早上 9 点，把各渠道的经营数据汇总成一份日报，包含昨日关键指标、与上周同期的对比、缺失或异常的数据项。汇总数字要能回溯到原始记录。' },
  { name: '内容选题助手', task: '选题与内容草稿生成', role: '内容', frequency: 'weekly_multi', duration: 't60',
    sources: ['web', 'file'], group: '内容创作', desc: '按周产出选题库与内容草稿，每条附来源链接，人工确认后发布。',
    prompt: '每周二和周五各出一批选题，围绕我所在的行业，每条选题给出 5 个备选标题和一段内容草稿，并附上参考来源链接。发布前我会人工确认，不要直接发出去。' },
  { name: '学习计划拆解', task: '学习计划拆解与资料整理', role: '研发', frequency: 'weekly', duration: 't60',
    sources: ['file', 'web'], group: '学习成长', desc: '把学习目标拆成可执行计划，整理笔记与复盘表。',
    prompt: '我准备学一个新方向，请帮我把目标拆成每周可执行的计划，每项带截止时间；同时整理相关资料要点，每周日晚上输出一份复盘，包含本周完成情况和下周要补的。' },
  { name: '简历初筛', task: '简历筛选与候选人初评', role: '人力', frequency: 'daily', duration: 't30',
    sources: ['file', 'mail'], group: '人力资源', desc: '按岗位要求筛选简历，给出匹配度与理由，标注硬性条件缺口。',
    prompt: '这是我这个岗位的 JD 和一批简历，请逐份对照 JD 给出匹配度评分和理由，把不满足硬性条件（学历、年限、必备技能）的直接标出来，并为通过初筛的人各生成 3 个面试问题。联系候选人之前我会自己复核。' },
  { name: '报销单核对', task: '发票与报销单核对', role: '财务', frequency: 'weekly_multi', duration: 't60',
    sources: ['file', 'sheet'], group: '财务法务', desc: '逐条比对报销单与发票，标出金额、抬头、日期不一致的条目。',
    prompt: '这是本期的报销单和对应发票，请逐条核对金额、抬头、日期和事由是否一致，把不一致的项单独列出来并说明差异。只做核对，不要修改任何财务系统里的数据。' },
  { name: '证照到期提醒', task: '合同与证照到期提醒', role: '行政', frequency: 'weekly', duration: 't30',
    sources: ['file', 'sheet'], group: '财务法务', desc: '巡检合同与资质证照有效期，提前 30 天给出提醒与续签材料清单。',
    prompt: '这是我们公司所有在执行的合同和资质证照台账，请按到期时间排序，把 30 天内到期的挑出来提醒我，并给每一项列出续签需要准备的材料清单，注明原始文件放在哪里。' },
  { name: '会议纪要', task: '会议纪要与待办跟踪', role: '行政', frequency: 'daily_multi', duration: 't30',
    sources: ['file', 'chat'], group: '协作沟通', desc: '把会议录音或记录整理成纪要，分离决议与待办，待办带负责人和截止日。',
    prompt: '这是我们这次会议的录音转写稿，请整理成纪要：先写会议结论和达成的决议，再单独列出待办事项，每条待办标注负责人和截止日期。整理完先给我确认，我确认后再发给参会人。' },
  { name: '供应商比价', task: '供应商比价与询价整理', role: '采购', frequency: 'weekly_multi', duration: 't60',
    sources: ['web', 'sheet'], group: '采购供应', desc: '把多家供应商报价整理成同口径比价表，给出议价建议。',
    prompt: '这是几家供应商的报价单，请按同一规格和含税口径整理成比价表，算出单价差异百分比，并给出建议的议价空间。不要代替我对外发询价邮件，我只用这份表做内部决策。' },
  { name: '工单聚类分析', task: '工单聚类与根因初判', role: '客服', frequency: 'daily', duration: 't60',
    sources: ['api', 'chat'], group: '客户服务', desc: '把当日工单聚类，输出高频问题排行与根因初判。',
    prompt: '这是今天的客服工单，请按问题症状聚类，输出高频问题排行，每个高频问题附上 2~3 个代表性工单号，并给出可能的根因初判。聚类口径要写清楚，根因结论我会人工确认。' },
  { name: '政策动态监测', task: '行业政策与舆情监测', role: '市场', frequency: 'daily', duration: 't30',
    sources: ['web', 'mail'], group: '市场运营', desc: '每日监测行业政策与舆情，附原文链接并做影响面分级。',
    prompt: '每天上午帮我看一遍我所在行业的最新政策和舆情动态，重要的整理成摘要，每条附上原文链接，并按对我们的影响程度分成高中低三档。没有核实过的消息不要转发。' },
  { name: '评价口碑分析', task: '用户评价汇总与情感分析', role: '市场', frequency: 'weekly_multi', duration: 't30',
    sources: ['web', 'api'], group: '市场运营', desc: '汇总各平台用户评价，做情感分布与典型差评归因。',
    prompt: '把这些平台的用户评价汇总一下，先分正面和负面，统计各自的占比和主要话题；负面评价里挑出典型差评附上原文，并给出可以落到具体环节的改进建议。' },
  { name: '知识库问答对', task: '内部知识库问答对整理', role: '其他', frequency: 'weekly_multi', duration: 't60',
    sources: ['file', 'chat'], group: '知识管理', desc: '把散落的文档和群聊问答整理成标准问答对，便于后续检索复用。',
    prompt: '这是我们团队这一周的群聊问答和一些内部文档，请把反复被问到的问题整理成标准问答对，答案要简洁准确并注明出处；拿不准的先标成“待确认”，不要自己编答案。' },
  { name: '项目周报汇总', task: '多项目周报汇总', role: '项目管理', frequency: 'weekly', duration: 't60',
    sources: ['chat', 'sheet', 'api'], group: '协作沟通', desc: '汇总多个项目的本周进展、风险与下周计划，生成统一格式周报。',
    prompt: '这是我们几个项目本周的记录，请汇总成一份周报：每个项目写清本周进展、当前风险、下周计划和需要协调的事项。风险项要标出影响面和责任人，数字部分要和原始记录对得上。' }
]

const CUSTOM_PROMPT_KEY = 'yixiu-service-prompts'
const readCustomPrompts = () => {
  try {
    const raw = JSON.parse(localStorage.getItem(CUSTOM_PROMPT_KEY) || '[]')
    return Array.isArray(raw) ? raw : []
  } catch (error) {
    return []
  }
}
const customPrompts = ref(readCustomPrompts())
const OPTIMIZE_KEY = 'yixiu-service-prompt-overrides'
const readOverrides = () => {
  try {
    const raw = JSON.parse(localStorage.getItem(OPTIMIZE_KEY) || '{}')
    return raw && typeof raw === 'object' ? raw : {}
  } catch (error) {
    return {}
  }
}
const promptOverrides = ref(readOverrides())
const optimizeTarget = ref(null)
const optimizeText = ref('')

const persistOverrides = (next) => {
  try { localStorage.setItem(OPTIMIZE_KEY, JSON.stringify(next)) } catch (error) { /* 忽略配额错误 */ }
}

const openOptimize = (item) => {
  optimizeTarget.value = item
  optimizeText.value = item.prompt
}

const saveOptimize = () => {
  const target = optimizeTarget.value
  const text = optimizeText.value.trim()
  if (!target || !text) return
  if (target.custom) {
    const next = customPrompts.value.map((p) => (p.name === target.name ? { ...p, prompt: text } : p))
    customPrompts.value = next
    try { localStorage.setItem(CUSTOM_PROMPT_KEY, JSON.stringify(next)) } catch (error) { /* 忽略 */ }
  } else {
    const next = { ...promptOverrides.value, [target.name]: text }
    promptOverrides.value = next
    persistOverrides(next)
  }
  optimizeTarget.value = null
  flash(`已保存「${target.name}」的优化版本`)
}

const resetOptimize = (item) => {
  const next = { ...promptOverrides.value }
  delete next[item.name]
  promptOverrides.value = next
  persistOverrides(next)
  flash(`已恢复「${item.name}」的默认提示词`)
}

const promptGroup = ref('全部')
const promptGroupList = computed(() => {
  const groups = [...new Set(allPrompts.value.filter((p) => !p.custom && p.group).map((p) => p.group))]
  const mine = allPrompts.value.some((p) => p.custom)
  return ['全部', ...(mine ? ['我的'] : []), ...groups]
})
const promptCountIn = (group) => (group === '我的'
  ? allPrompts.value.filter((p) => p.custom).length
  : allPrompts.value.filter((p) => p.group === group).length)
const visiblePrompts = computed(() => {
  if (promptGroup.value === '全部') return allPrompts.value
  if (promptGroup.value === '我的') return allPrompts.value.filter((p) => p.custom)
  return allPrompts.value.filter((p) => p.group === promptGroup.value)
})

const showPromptForm = ref(false)
const promptForm = reactive({ title: '', text: '' })
const allPrompts = computed(() => {
  const overrides = promptOverrides.value
  return [
    ...PROMPTS.map((item) => (overrides[item.name]
      ? { ...item, prompt: overrides[item.name], optimized: true }
      : item)),
    ...customPrompts.value.map((item) => ({ ...item, custom: true }))
  ]
})

const savePrompt = () => {
  if (!promptForm.title || !promptForm.text) return
  const next = [{ name: promptForm.title, desc: '我自己保存的提示词', prompt: promptForm.text }, ...customPrompts.value]
  customPrompts.value = next
  try { localStorage.setItem(CUSTOM_PROMPT_KEY, JSON.stringify(next)) } catch (error) { /* 忽略配额错误 */ }
  promptForm.title = ''
  promptForm.text = ''
  showPromptForm.value = false
  flash('已保存到我的提示词')
}

const deletePrompt = (item) => {
  const next = customPrompts.value.filter((p) => p.name !== item.name)
  customPrompts.value = next
  try { localStorage.setItem(CUSTOM_PROMPT_KEY, JSON.stringify(next)) } catch (error) { /* 忽略 */ }
  flash('已删除')
}

const copyPromptText = async (item) => {
  try {
    await navigator.clipboard.writeText(item.prompt)
    flash(`已复制「${item.name}」`)
  } catch (error) {
    flash('浏览器未授权剪贴板，请手动复制')
  }
}

const freqLabel = (key) => (options.value.frequency.find((f) => f.key === key) || {}).label || key
const durationLabel = (key) => (options.value.duration.find((d) => d.key === key) || {}).label || key


const applyTemplate = (app) => {
  intake.role = app.role
  intake.tasks = [app.task]
  intake.frequency = app.frequency
  intake.duration = app.duration
  intake.sources = [...app.sources]
  intake.note = ''
  report.value = null
  mode.value = 'guided'
  panel.value = 'diagnose'
  step.value = STEPS.length - 1
  flash(`已套用「${app.name}」，直接生成体检报告即可`)
}

const canNext = computed(() => {
  const key = STEPS[step.value].key
  if (key === 'role') return Boolean(intake.role)
  if (key === 'tasks') return intake.tasks.length > 0
  if (key === 'frequency') return Boolean(intake.frequency)
  if (key === 'duration') return Boolean(intake.duration)
  return intake.sources.length > 0
})

const toggleIn = (arr, value) => {
  const idx = arr.indexOf(value)
  if (idx === -1) arr.push(value)
  else arr.splice(idx, 1)
}

const ringStyle = (score) => ({
  background: `conic-gradient(#1f7a6f ${Math.max(0, Math.min(100, Number(score) || 0))}%, #e8eef1 0)`
})

const verdictTone = computed(() => {
  const v = String(report.value?.verdict || '')
  if (v.includes('建议开通')) return 'good'
  if (v.includes('不托管') || v.includes('标准化')) return 'warn'
  return 'mid'
})

const loadOptions = async () => {
  optionsLoading.value = true
  try {
    options.value = await yixiuApi.serviceIntakeOptions()
  } catch (error) {
    // 选项拉取失败时保持空数组：canNext 会拦住下一步，页面给出重启后端的提示
  } finally {
    optionsLoading.value = false
  }
}

const submitIntake = async () => {
  busy.value = true
  try {
    const data = await yixiuApi.serviceIntake({ account: props.account, project: '需求体检', intake: { ...intake } })
    report.value = data.report || null
    if (!report.value || !report.value.ready) flash('信息不足，建议返回补充重复事项')
  } catch (error) {
    flash('体检服务不可用，请确认后端已启动')
  } finally {
    busy.value = false
  }
}

const resetIntake = () => {
  report.value = null
  step.value = 0
}

const copyReport = async (d) => {
  const a = d.automation || {}
  const dims = d.dimensions || {}
  const lines = [
    `需求体检结论：${report.value?.verdict || ''}`,
    `推荐岗位：${d.position}`,
    `可行性评分：${d.feasibility}/100（频次 ${dims.frequency}｜规则化 ${dims.regularity}｜数据可得性 ${dims.data}｜单次耗时 ${dims.timeCost}）`,
    `每周节省：${a.savedHoursPerWeek} 小时｜每月节省：¥${a.monthlySaving}`,
    `托管费：¥${a.monthlyCost}/月｜净收益：¥${a.netBenefit}/月｜回本：${a.paybackDays} 天`,
    '',
    '落地路径：',
    ...(d.rollout || []).flatMap((w) => [`${w.week} ${w.title}`, ...(w.items || []).map((it) => `  · ${it}`)]),
    '',
    '前置条件：',
    ...(d.prerequisites || []).map((p) => `  · ${p.item}：${p.note}`)
  ]
  try {
    await navigator.clipboard.writeText(lines.join('\n'))
    flash('方案已复制到剪贴板')
  } catch (e) {
    flash('浏览器未授权剪贴板，请手动复制')
  }
}

onMounted(() => { loadHostings(); loadOptions() })
watch(panel, (v) => { if (v === 'hosting') loadHostings() })
</script>

<style scoped>
.service-desk { display: grid; gap: 16px; align-content: start; }
/* 四个子元素：页头 / 模式切换 / 正文 / Skill 推荐榜。推荐榜只占自身高度，
   正文用 1fr 吸收剩余空间，避免推荐榜把体检流程挤扁。 */
.service-desk.sd-chat-mode { grid-template-rows: auto auto minmax(0, 1fr) auto; height: 100%; min-height: 0; align-content: stretch; }

.sd-hero {
  display: flex; align-items: flex-end; justify-content: space-between; gap: 20px;
  padding: 20px 22px; border: 1px solid #ece0c8; border-radius: 18px;
  background: linear-gradient(135deg, #fffdf7 0%, #fdf7e9 100%);
}
.sd-eyebrow { margin: 0; color: var(--amber); font-size: 11px; font-weight: 900; letter-spacing: .16em; }
.sd-hero h2 { margin: 6px 0 4px; color: #3d2f14; font-size: 24px; }
.sd-sub { margin: 0; color: #8a7a5c; font-size: 12.5px; }

/* 按页签数量自适应一行：原来是写死的 1fr 1fr，加到第三个页签（教程·应用）就换行了 */
.sd-tabs { display: grid; grid-auto-flow: column; grid-auto-columns: minmax(0, 1fr); gap: 4px; padding: 4px; border-radius: 12px; background: #f4ead4; }
.sd-tabs button {
  position: relative; min-height: 38px; padding: 0 18px; border: 0; border-radius: 9px; background: transparent;
  color: #8a7a5c; font-size: 12.5px; font-weight: 800; cursor: pointer;
}
.sd-tabs button.active { background: #fff; color: var(--amber); box-shadow: 0 5px 14px rgba(151,102,27,.14); }
.sd-tabs button em {
  position: absolute; top: 3px; right: 5px; min-width: 15px; height: 15px; padding: 0 4px;
  display: grid; place-items: center; border-radius: 999px;
  background: #fbe8e4; color: #b44c43; font-size: 9.5px; font-style: normal; font-weight: 900;
}

/* ---------- 需求体检 ---------- */
.sd-chat {
  display: grid; grid-template-rows: auto minmax(0, 1fr) auto auto;
  gap: 12px; min-height: 0; padding: 18px 22px 20px;
  border: 1px solid #e7e3da; border-radius: 18px; background: #fff;
  box-shadow: 0 10px 30px rgba(143,120,73,.06);
}
.sd-chat-head { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; gap: 12px; align-items: center; padding-bottom: 12px; border-bottom: 1px solid #f2ede2; }
.sd-chat-head > div:not(.sd-tools) { display: grid; gap: 2px; }
.sd-chat-head b { color: #3d2f14; font-size: 14px; }
.sd-chat-head small { color: #9a9080; font-size: 11.5px; }

.sd-tools { display: flex; align-items: center; gap: 6px; }
.sd-tools > small { color: #b3a894; font-size: 10.5px; }
.sd-tool { display: grid; place-items: center; width: 26px; height: 26px; border: 1px solid #efe7d6; border-radius: 8px; background: #fffdf8; }
.sd-tool img { width: 15px; height: 15px; object-fit: contain; }

.sd-thread { display: grid; gap: 14px; align-content: start; overflow-y: auto; padding: 4px 8px 4px 2px; }
.sd-msg { display: flex; gap: 10px; align-items: flex-start; max-width: 900px; }
.sd-bubble { max-width: 800px; border-radius: 14px; }
.sd-msg.assistant .sd-bubble { background: #f7f4ec; }
.sd-msg.user .sd-bubble { background: #16766f; }
.sd-msg p { margin: 0; padding: 12px 15px; font-size: 13px; line-height: 1.75; white-space: pre-line; }
.sd-msg.assistant p { color: #4a3f2a; }
.sd-msg.user { flex-direction: row-reverse; margin-left: auto; }
.sd-msg.user p { color: #fff; }
.sd-msg p.typing { color: #9a9080; }
.sd-ava { flex: 0 0 30px; width: 30px; height: 30px; border-radius: 50%; object-fit: cover; background: #f4ece0; border: 1px solid #ece0c8; }
.sd-ava.big { flex: 0 0 44px; width: 44px; height: 44px; }

.sd-diag { display: grid; gap: 12px; padding: 0 15px 14px; }
.sd-diag-tasks { display: grid; gap: 6px; margin: 0; padding: 0; list-style: none; }
.sd-diag-tasks li { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 8px 11px; border-radius: 9px; background: #fff; }
.sd-diag-tasks span { color: #4a3f2a; font-size: 12.5px; }
.sd-diag-tasks em { padding: 2px 8px; border-radius: 999px; font-size: 10.5px; font-style: normal; font-weight: 800; }
.sd-diag-tasks em.high { background: #fbe8e4; color: #b44c43; }
.sd-diag-tasks em.mid { background: #fdf1d8; color: #a06a1c; }
.sd-diag-meta { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.sd-diag-meta span { display: grid; gap: 2px; padding: 9px 10px; border-radius: 9px; background: #fff; }
.sd-diag-meta small { color: #a89e8c; font-size: 10.5px; }
.sd-diag-meta b { color: #3d2f14; font-size: 12px; }
.sd-diag-actions { display: flex; gap: 8px; }
.sd-diag-actions button { min-height: 34px; padding: 0 16px; border: 1px solid #e6dcc4; border-radius: 9px; background: #fff; color: #6b5220; font-size: 12px; font-weight: 800; cursor: pointer; }
.sd-diag-actions button.primary { border: 0; background: linear-gradient(135deg, #c8872e, #e0a94a); color: #fff; }
.sd-diag-actions button:disabled { opacity: .55; cursor: not-allowed; }


.sd-input { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; }
.sd-input input { height: 50px; padding: 0 16px; border: 1px solid #eadfc6; border-radius: 12px; background: #fffdf8; color: #3d2f14; font-size: 13.5px; outline: 0; }
.sd-input input:focus { border-color: #d2a94f; box-shadow: 0 0 0 3px rgba(200,135,46,.14); }
.sd-input button { min-width: 96px; border: 0; border-radius: 12px; background: linear-gradient(135deg, #c8872e, #e0a94a); color: #fff; font-size: 13.5px; font-weight: 800; cursor: pointer; }
.sd-input button:disabled { opacity: .55; cursor: not-allowed; }
/* 浮动提示：组件根级渲染，任何面板都能看到，且不占布局空间 */
.sd-toast { position: fixed; right: 24px; bottom: 24px; z-index: 60; margin: 0; padding: 10px 16px;
  border-radius: 10px; background: #16766f; color: #fff; font-size: 12px; font-weight: 700;
  box-shadow: 0 10px 28px rgba(22,118,111,.28); }

/* ---------- 托管运行 ---------- */
.sd-card { display: grid; gap: 14px; align-content: start; padding: 18px; border: 1px solid #e7e3da; border-radius: 16px; background: #fff; box-shadow: 0 10px 30px rgba(143,120,73,.06); }
.sd-card > header { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; }
.sd-card > header b { color: #3d2f14; font-size: 14px; }
.sd-card > header small { color: #9a9080; font-size: 11.5px; }

.sd-hosting { display: grid; gap: 16px; }
.sd-kpis { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)) auto; gap: 12px; align-items: stretch; }
.sd-kpis > span { display: grid; gap: 3px; padding: 14px 16px; border: 1px solid #e7e3da; border-radius: 14px; background: #fff; }
.sd-kpis b { color: #3d2f14; font-size: 20px; }
.sd-kpis small { color: #9a9080; font-size: 11.5px; }
.sd-kpis > span.warn b { color: #b44c43; }
.sd-kpi-btn { padding: 0 18px; border: 1px solid #d2a94f; border-radius: 14px; background: #fffdf8; color: #a06a1c; font-size: 12.5px; font-weight: 800; cursor: pointer; }
.sd-kpi-btn:hover { background: #fdf4e2; }

/* 托管面板顶部的体检结论卡：把「体检 → 开通托管」这条链路接上，
   否则开通后看不到当初算出来的收益，也无法对照 */
.sd-host-brief { display: grid; grid-template-columns: minmax(0, 1.5fr) auto auto; gap: 16px; align-items: center;
  padding: 16px 18px; border: 1px solid #e7e3da; border-radius: 16px; background: #fff;
  box-shadow: 0 10px 30px rgba(143,120,73,.06); }
.sd-host-brief-copy h3 { margin: 2px 0 4px; color: #3a3226; font-size: 17px; }
.sd-host-brief-copy small { color: #8d8577; font-size: 11.5px; line-height: 1.6; }
.sd-host-brief-metrics { display: flex; flex-wrap: wrap; gap: 8px; }
.sd-host-brief-metrics span { display: grid; gap: 2px; padding: 8px 12px; border-radius: 10px; background: #f8fafb; }
.sd-host-brief-metrics small { color: #8d8577; font-size: 10.5px; }
.sd-host-brief-metrics b { color: #2f474e; font-size: 14px; }
.sd-host-brief-metrics span.neg b { color: #b0641c; }
.sd-host-brief > button { padding: 8px 14px; border: 1px solid #e7e3da; border-radius: 9px; background: #fff;
  color: #4a4237; font: inherit; font-size: 11.5px; font-weight: 800; cursor: pointer; }
.sd-host-brief > button:hover { border-color: #c8872e; color: #a8681c; }
@media (max-width: 1100px) {
  .sd-host-brief { grid-template-columns: minmax(0, 1fr); }
}

.sd-create { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, .8fr) minmax(0, 1fr) minmax(0, .8fr) auto; gap: 12px; align-items: end; padding: 16px 18px; border: 1px solid #ece0c8; border-radius: 14px; background: #fdfaf3; }.sd-create label { display: grid; gap: 6px; color: #6b5220; font-size: 11.5px; font-weight: 800; }
.sd-create input, .sd-create select { height: 42px; padding: 0 12px; border: 1px solid #e6dcc4; border-radius: 10px; background: #fff; color: #3d2f14; font-size: 12.5px; outline: 0; }
.sd-create input:focus, .sd-create select:focus { border-color: #d2a94f; box-shadow: 0 0 0 3px rgba(200,135,46,.14); }
.sd-create > button { height: 42px; min-width: 96px; border: 0; border-radius: 10px; background: linear-gradient(135deg, #c8872e, #e0a94a); color: #fff; font-size: 12.5px; font-weight: 800; cursor: pointer; }
.sd-create > button:disabled { opacity: .5; cursor: not-allowed; }

.sd-host-grid { display: grid; grid-template-columns: minmax(0, 1.6fr) minmax(280px, 1fr); gap: 16px; align-items: start; }
.sd-host { display: grid; gap: 10px; padding: 12px; border: 1px solid #efe7d6; border-radius: 12px; background: #fffdf8; }
.sd-host.open { background: #fff; border-color: #e0d0ab; }
.sd-host-head { display: grid; grid-template-columns: 56px minmax(0, 1fr) auto; gap: 12px; align-items: center; cursor: pointer; }
.sd-host-thumb { width: 56px; height: 56px; border-radius: 10px; object-fit: cover; border: 1px solid #efe7d6; }
.sd-host-info { display: grid; gap: 4px; min-width: 0; }
.sd-host-info b { color: #3d2f14; font-size: 13px; }
.sd-host-info small { color: #9a9080; font-size: 11px; }
.sd-host-right { display: grid; gap: 3px; justify-items: end; text-align: right; }
.sd-host-right em { padding: 2px 8px; border-radius: 999px; background: #e9f2ec; color: #16766f; font-size: 10.5px; font-style: normal; font-weight: 800; }
.sd-host-right em.paused { background: #f2ece0; color: #8a7a5c; }
.sd-host-right small { color: #a89e8c; font-size: 11px; }
.sd-quota { height: 5px; border-radius: 999px; background: #f2ece0; overflow: hidden; }
.sd-quota i { display: block; height: 100%; border-radius: 999px; background: linear-gradient(90deg, #c8872e, #e0a94a); }
.sd-quota i.full { background: linear-gradient(90deg, #d98b80, #b44c43); }
.sd-quota-text { color: #a89e8c; }

.sd-runs { display: grid; gap: 10px; padding-top: 8px; border-top: 1px dashed #efe7d6; }
.sd-run-actions { display: flex; align-items: center; gap: 8px; }
.sd-run-actions button { min-height: 34px; padding: 0 14px; border: 1px solid #e6dcc4; border-radius: 9px; background: #fff; color: #6b5220; font-size: 11.5px; font-weight: 800; cursor: pointer; }
.sd-run-actions button.primary { border: 0; background: linear-gradient(135deg, #c8872e, #e0a94a); color: #fff; }
.sd-run-actions button:disabled { opacity: .55; cursor: not-allowed; }
.sd-run-actions small { color: #a89e8c; font-size: 10.5px; }
.sd-runs table { width: 100%; border-collapse: collapse; font-size: 11.5px; }
.sd-runs th, .sd-runs td { padding: 8px; text-align: left; border-bottom: 1px solid #f2eee4; vertical-align: top; white-space: nowrap; }
.sd-runs th:nth-child(5), .sd-runs td:nth-child(5) { white-space: normal; }
.sd-runs th { color: #9a9080; font-weight: 800; }
.sd-runs td { color: #5c5342; }
.sd-runs em { padding: 2px 7px; border-radius: 999px; font-style: normal; font-weight: 800; font-size: 10.5px; }
.sd-runs em.success { background: #e9f2ec; color: #16766f; }
.sd-runs em.warning { background: #fdf1d8; color: #a06a1c; }
.sd-artifact { display: inline-flex; align-items: center; gap: 5px; margin: 0 5px 4px 0; padding: 3px 8px 3px 4px; border: 1px solid #f0ece2; border-radius: 7px; background: #faf8f3; color: #6b5c3c; font-size: 10.5px; }
.sd-artifact i { padding: 1px 4px; border-radius: 4px; font-size: 8.5px; font-style: normal; font-weight: 900; }
.sd-artifact i.xls { background: #e3f1e7; color: #2f7d4f; }
.sd-artifact i.pdf { background: #fbe8e4; color: #b44c43; }
.sd-artifact i.txt { background: #eaf0f6; color: #3979b8; }
.sd-artifact i.file { background: #f0ece2; color: #7d7259; }
.sd-note { display: block; color: #b07a2a; font-size: 10.5px; }

.sd-board { display: grid; gap: 16px; }
.sd-board-block { display: grid; gap: 8px; }
.sd-board-block h4 { margin: 0; color: #8a7a5c; font-size: 11.5px; font-weight: 900; }
.sd-bars { display: flex; align-items: flex-end; gap: 4px; height: 76px; padding: 6px; border-radius: 10px; background: #faf8f3; }
.sd-bars i { flex: 1; min-height: 8px; border-radius: 3px 3px 0 0; background: linear-gradient(180deg, #7bb8a4, #16766f); }
.sd-bars i.low { background: linear-gradient(180deg, #e8b95e, #c8872e); }
.sd-axis { color: #a89e8c; font-size: 10.5px; }
.sd-warn { display: flex; gap: 8px; padding: 9px 11px; border-radius: 10px; background: #fdf1d8; color: #8a6520; font-size: 11.5px; line-height: 1.5; }
.sd-warn > div { display: grid; gap: 5px; }
.sd-warn button { justify-self: start; padding: 2px 9px; border: 1px solid #e0c48a; border-radius: 7px; background: #fff; color: #a06a1c; font-size: 10.5px; font-weight: 800; cursor: pointer; }
.sd-evi-list { display: grid; gap: 6px; margin: 0; padding: 0; list-style: none; }
.sd-evi-list li { display: flex; align-items: center; gap: 8px; padding: 8px 11px; border-radius: 9px; background: #f2f7f3; color: #2c6b5f; font-size: 11.5px; }
.sd-evi-list em { margin-left: auto; color: #7fa99f; font-style: normal; font-size: 10.5px; }

.sd-empty { display: grid; gap: 10px; justify-items: center; margin: 0; padding: 22px 16px; border: 1px dashed #e4dcc8; border-radius: 12px; color: #a89e8c; font-size: 12px; text-align: center; }
.sd-empty p { margin: 0; }
.sd-empty.small { padding: 10px; font-size: 11.5px; }
.sd-empty button { min-height: 34px; padding: 0 16px; border: 0; border-radius: 9px; background: linear-gradient(135deg, #c8872e, #e0a94a); color: #fff; font-size: 12px; font-weight: 800; cursor: pointer; }

/* ---------- 体检模式切换 ---------- */
.sd-modes { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.sd-modes button { display: grid; gap: 3px; padding: 12px 14px; border: 1px solid #e7e3da; border-radius: 14px;
  background: #fff; text-align: left; cursor: pointer; transition: border-color .18s, box-shadow .18s; }
.sd-modes button b { color: #3a3226; font-size: 13.5px; }
.sd-modes button small { color: #8d8577; font-size: 11px; line-height: 1.5; }
.sd-modes button.active { border-color: #c8872e; background: #fffdf8; box-shadow: 0 8px 20px rgba(200,135,46,.14); }
.sd-modes button.active b { color: #a8681c; }

/* ---------- 分步引导 ---------- */
.sd-guided { display: grid; gap: 14px; align-content: start; }
.sd-steps { display: flex; flex-wrap: wrap; gap: 8px; }
.sd-steps span { display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border: 1px solid #e7e3da;
  border-radius: 999px; background: #fff; color: #8d8577; font-size: 11.5px; }
.sd-steps span em { width: 18px; height: 18px; display: grid; place-items: center; border-radius: 50%;
  background: #f1ece2; color: #8d8577; font-size: 10.5px; font-style: normal; font-weight: 800; }
.sd-steps span.on { border-color: #c8872e; color: #a8681c; }
.sd-steps span.on em { background: #c8872e; color: #fff; }
.sd-steps span.done em { background: #16766f; color: #fff; }

.sd-form { display: grid; gap: 12px; padding: 20px; border: 1px solid #e7e3da; border-radius: 16px; background: #fff;
  box-shadow: 0 10px 30px rgba(143,120,73,.06); }
.sd-form h3 { margin: 0; color: #3a3226; font-size: 17px; }

.sd-guide-hero { padding: 18px 20px; border-left: 4px solid #1c837a; border-radius: 12px; background: linear-gradient(135deg, #f4faf9, #f7fbfb); }
.sd-guide-hero b { display: block; margin-bottom: 4px; color: #3d2f14; font-size: 14px; }
.sd-guide-hero small { color: #8d8577; font-size: 11.5px; line-height: 1.6; }

/* 每一步：配图 + 「为什么问这个」。这张卡原来是单列，右侧大片留白。 */
.sd-form-head { display: grid; grid-template-columns: 168px minmax(0, 1fr); gap: 16px; align-items: start; }
.sd-form-headcopy { display: grid; gap: 5px; min-width: 0; }
.sd-why { margin: 3px 0 0; padding: 8px 11px; border-left: 3px solid #e0c690; border-radius: 0 9px 9px 0;
  background: #fdfaf3; color: #6d6559; font-size: 11.5px; line-height: 1.65; }
.sd-why b { margin-right: 6px; color: #a8681c; font-size: 11px; font-weight: 800; }
.sd-hint { margin: 0; color: #8d8577; font-size: 12px; }
.sd-hint-warn { padding: 9px 12px; border: 1px solid #f0dcc0; border-radius: 10px; background: #fff9f2; color: #a8681c; }
.sd-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.sd-chips.wide { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); }
.sd-chips button { display: grid; gap: 2px; padding: 10px 14px; border: 1px solid #e7e3da; border-radius: 12px;
  background: #fff; color: #4a4237; font-size: 13px; font-weight: 700; text-align: left; cursor: pointer; }
.sd-chips button em { color: #a89e8c; font-size: 10.5px; font-style: normal; font-weight: 600; }
.sd-chips button.on { border-color: #c8872e; background: #fffdf8; color: #a8681c; }
.sd-note { display: grid; gap: 5px; grid-column: 1 / -1; color: #8d8577; font-size: 11.5px; font-weight: 700; }
.sd-note input { padding: 10px 12px; border: 1px solid #e7e3da; border-radius: 10px; font: inherit; font-size: 12.5px; font-weight: 400; }
.sd-form-foot { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding-top: 4px; }
.sd-form-foot button { min-width: 92px; padding: 10px 16px; border: 1px solid #e7e3da; border-radius: 10px;
  background: #fff; color: #4a4237; font: inherit; font-size: 12.5px; font-weight: 800; cursor: pointer; }
.sd-form-foot button.primary { border: 0; background: linear-gradient(135deg, #c8872e, #e0a94a); color: #fff; }
.sd-form-foot button:disabled { opacity: .5; cursor: not-allowed; }
.sd-progress { color: #a89e8c; font-size: 11.5px; font-weight: 700; }

/* ---------- 体检报告 ---------- */
.sd-report { display: grid; gap: 12px; }
.sd-verdict { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; padding: 16px 18px;
  border: 1px solid #e7e3da; border-left: 5px solid #8d8577; border-radius: 14px; background: #fff; }
.sd-verdict.good { border-left-color: #16766f; background: #f7fcfb; }
.sd-verdict.mid { border-left-color: #c8872e; background: #fffdf8; }
.sd-verdict.warn { border-left-color: #b0641c; background: #fff9f2; }
.sd-verdict h3 { margin: 2px 0 4px; color: #3a3226; font-size: 18px; }
.sd-verdict p { margin: 0; max-width: 720px; color: #6d6559; font-size: 12.5px; line-height: 1.62; }
.sd-verdict button { flex: none; padding: 8px 14px; border: 1px solid #e7e3da; border-radius: 9px; background: #fff;
  color: #4a4237; font: inherit; font-size: 11.5px; font-weight: 800; cursor: pointer; }

.sd-report-grid { display: grid; gap: 12px; }
.sd-report-card { display: grid; gap: 12px; padding: 16px 18px; border: 1px solid #e7e3da; border-radius: 16px;
  background: #fff; box-shadow: 0 10px 30px rgba(143,120,73,.06); }
.sd-report-card.top { border-color: #d9c9a4; }
.sd-report-card > header { display: flex; align-items: center; justify-content: space-between; gap: 14px; }
.sd-report-card > header b { display: block; color: #3a3226; font-size: 15px; }
.sd-report-card > header small { color: #8d8577; font-size: 11.5px; }
.sd-ring { position: relative; display: grid; place-items: center; width: 62px; height: 62px; border-radius: 50%; flex: none; padding: 0; }
.sd-ring em { position: relative; z-index: 1; color: #16766f; font-size: 17px; font-style: normal; font-weight: 900; line-height: 1; }
.sd-ring small { position: relative; z-index: 1; color: #6d6559; font-size: 9px; }
.sd-ring::before { content: ''; position: absolute; inset: 7px; border-radius: 50%; background: #fff; }

.sd-dims { display: grid; gap: 6px; }
.sd-dims span { display: grid; grid-template-columns: 78px minmax(0, 1fr) 34px; align-items: center; gap: 10px; }
.sd-dims small { color: #8d8577; font-size: 11px; }
.sd-dims i { display: block; height: 7px; border-radius: 999px; background: #eef2f4; overflow: hidden; }
.sd-dims i b { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #7fb3a8, #16766f); }
.sd-dims em { color: #4a4237; font-size: 11.5px; font-style: normal; font-weight: 800; text-align: right; }

.sd-roi { display: flex; flex-wrap: wrap; gap: 8px; }
.sd-roi span { flex: 1 1 92px; display: grid; gap: 2px; padding: 9px 11px; border-radius: 10px; background: #f8fafb; }
.sd-roi small { color: #8d8577; font-size: 10px; }
.sd-roi b { color: #2f474e; font-size: 13.5px; }
.sd-roi span.neg b { color: #b0641c; }

.sd-report-card details { border-top: 1px solid #f0ece4; padding-top: 8px; }
.sd-report-card summary { color: #6d6559; font-size: 12px; font-weight: 800; cursor: pointer; }
.sd-plan { display: grid; gap: 8px; margin: 8px 0 0; padding-left: 16px; }
.sd-plan b { color: #3a3226; font-size: 12px; }
.sd-plan ul, .sd-accept { margin: 4px 0 0; padding-left: 16px; color: #6d6559; font-size: 11.5px; line-height: 1.65; }
.sd-prereq { display: grid; gap: 5px; margin: 8px 0 0; padding: 0; list-style: none; }
.sd-prereq li { display: grid; gap: 2px; padding: 7px 10px; border-radius: 9px; background: #f7fbfa; }
.sd-prereq li.miss { background: #fff9f2; }
.sd-prereq b { color: #3a3226; font-size: 11.5px; }
.sd-prereq small { color: #8d8577; font-size: 10.5px; }
.sd-report-actions { display: flex; flex-wrap: wrap; gap: 8px; }
.sd-report-actions button { padding: 9px 14px; border: 1px solid #e7e3da; border-radius: 10px; background: #fff;
  color: #4a4237; font: inherit; font-size: 12px; font-weight: 800; cursor: pointer; }
.sd-report-actions button.primary { border: 0; background: linear-gradient(135deg, #c8872e, #e0a94a); color: #fff; }
.sd-risks { display: grid; gap: 5px; margin: 0; padding: 14px 18px 14px 34px; border: 1px dashed #e4dcc8;
  border-radius: 14px; color: #8d8577; font-size: 11.5px; line-height: 1.6; }

@media (max-width: 1400px) {
  .sd-create { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .sd-create > button { grid-column: 2 / 3; }
}
@media (max-width: 1100px) {
  .sd-host-grid { grid-template-columns: minmax(0, 1fr); }
  .sd-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .sd-diag-meta { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
/* ---------- 教程 · 应用 ---------- */
.sd-learn { display: grid; gap: 16px; align-content: start; }
.sd-learn-block { display: grid; gap: 12px; padding: 18px 20px; border: 1px solid #e7e3da; border-radius: 16px;
  background: #fff; box-shadow: 0 10px 30px rgba(143,120,73,.06); }
.sd-learn-block > header h3 { margin: 2px 0 4px; color: #3a3226; font-size: 17px; }
.sd-learn-block > header small { color: #8d8577; font-size: 12px; line-height: 1.6; }
.sd-app-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
.sd-app { display: grid; gap: 8px; align-content: start; padding: 14px 16px; border: 1px solid #eee7da;
  border-radius: 13px; background: #fff; }
.sd-app b { color: #3a3226; font-size: 14px; }
.sd-app p { margin: 0; color: #6d6559; font-size: 11.5px; line-height: 1.6; }
.sd-app-meta { display: grid; gap: 3px; }
.sd-app-meta span { color: #a89e8c; font-size: 10.5px; }
.sd-app button { margin-top: 4px; padding: 8px 14px; border: 1px solid #e7e3da; border-radius: 9px; background: #fff;
  color: #4a4237; font: inherit; font-size: 12px; font-weight: 800; cursor: pointer; }
.sd-app button.primary { border: 0; background: linear-gradient(135deg, #c8872e, #e0a94a); color: #fff; }
.sd-app button:disabled { opacity: .55; cursor: not-allowed; }

/* ---------- Skill 推荐榜（服务台首页） ---------- */
.sd-rank { display: grid; gap: 10px; padding: 16px 18px; border: 1px solid #e7e3da; border-radius: 16px;
  background: #fff; box-shadow: 0 10px 30px rgba(143,120,73,.06); }
.sd-rank > header { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; }
.sd-rank > header h3 { margin: 2px 0 4px; color: #3a3226; font-size: 16px; }
.sd-rank > header small { color: #8d8577; font-size: 11.5px; line-height: 1.6; }
.sd-rank > header button { flex: none; padding: 7px 13px; border: 1px solid #e7e3da; border-radius: 9px; background: #fff;
  color: #4a4237; font: inherit; font-size: 11.5px; font-weight: 800; cursor: pointer; }
.sd-rank-list { display: grid; gap: 4px; }
.sd-rank-list a { display: grid; grid-template-columns: 30px minmax(0, 1.6fr) 92px minmax(120px, .8fr) 16px;
  align-items: center; gap: 12px; padding: 8px 10px; border-radius: 10px; background: #fbfaf7;
  color: inherit; text-decoration: none; }
.sd-rank-list a:hover { background: #f6f2ea; }
.sd-rank-list em { width: 26px; height: 26px; display: grid; place-items: center; border-radius: 8px;
  background: #f1ece2; color: #8d8577; font-size: 11px; font-style: normal; font-weight: 900; }
.sd-rank-list em.hot { background: #eef5f4; color: #16766f; }
.sd-rank-list em.warm { background: #fff4e6; color: #a8681c; }
.sd-rank-main { display: grid; gap: 1px; min-width: 0; }
.sd-rank-main b { color: #3a3226; font-size: 12.5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sd-rank-main small { color: #a89e8c; font-size: 10.5px; }
.sd-rank-stars { display: inline-flex; align-items: center; gap: 4px; color: #4a4237; font-size: 11.5px; font-weight: 800; }
.sd-rank-stars i { color: #c8a45c; font-style: normal; }
.sd-rank-match { display: grid; gap: 4px; }
.sd-rank-match b { color: #16766f; font-size: 11px; }
.sd-rank-match i { display: block; height: 5px; border-radius: 999px; background: #eef2f1; overflow: hidden; }
.sd-rank-match i u { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #7fb3a8, #16766f); }
.sd-rank-arrow { color: #c0b8a8; font-size: 12px; text-align: right; }
@media (max-width: 1000px) {
  .sd-rank-list a { grid-template-columns: 30px minmax(0, 1fr) 84px 16px; }
  .sd-rank-match { display: none; }
}

@media (max-width: 900px) {
  .sd-modes { grid-template-columns: minmax(0, 1fr); }
  .sd-chips.wide { grid-template-columns: minmax(0, 1fr); }
  .sd-verdict { flex-direction: column; }
  .sd-report-card > header { flex-wrap: wrap; }
  .sd-guide-hero { grid-template-columns: minmax(0, 1fr); }
  .sd-form-head { grid-template-columns: minmax(0, 1fr); }
}

/* ---------- 提示词 ---------- */
.sd-prompt-form {
  display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 2fr); gap: 12px;
  padding: 16px 18px; border: 1px solid #ece0c8; border-radius: 14px; background: #fdfaf3;
}
.sd-prompt-form label { display: grid; gap: 6px; color: #6b5220; font-size: 11.5px; font-weight: 800; }
.sd-prompt-form .wide { grid-column: 1 / -1; }
.sd-prompt-form input, .sd-prompt-form textarea {
  width: 100%; padding: 11px 13px; border: 1px solid #e6dcc4; border-radius: 10px;
  background: #fff; color: #3d2f14; font: inherit; font-size: 12.5px; line-height: 1.7; outline: 0;
}
.sd-prompt-form input:focus, .sd-prompt-form textarea:focus { border-color: #d2a94f; box-shadow: 0 0 0 3px rgba(200,135,46,.14); }
.sd-prompt-form textarea { min-height: 96px; resize: vertical; }
.sd-prompt-form-foot { grid-column: 1 / -1; display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.sd-prompt-form-foot small { color: #a89e8c; font-size: 11.5px; }
.sd-prompt-form-foot button {
  min-height: 38px; padding: 0 20px; border: 0; border-radius: 10px;
  background: linear-gradient(135deg, #c8872e, #e0a94a); color: #fff; font-size: 12.5px; font-weight: 800; cursor: pointer;
}
.sd-prompt-form-foot button:disabled { opacity: .5; cursor: not-allowed; }

.sd-prompt-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(330px, 1fr)); gap: 14px; }
.sd-prompt { display: grid; gap: 10px; align-content: start; padding: 16px; border: 1px solid #ece7dc; border-radius: 14px; background: #fff; }
.sd-prompt.custom { border-color: #e0d0ab; background: #fffdf8; }
.sd-prompt > header { display: flex; align-items: center; gap: 8px; }
.sd-prompt > header b { color: #3d2f14; font-size: 13.5px; }
.sd-prompt > header em { padding: 2px 8px; border-radius: 999px; background: #fdf1d8; color: #a06a1c; font-size: 10.5px; font-style: normal; font-weight: 800; }
.sd-prompt-desc { margin: 0; color: #8a7a5c; font-size: 12px; line-height: 1.6; }
.sd-prompt-text {
  display: block; max-height: 112px; overflow: auto; padding: 11px 12px;
  border: 1px solid #efe9dd; border-radius: 10px; background: #fbfaf7;
  color: #5c5342; font-family: inherit; font-size: 12px; line-height: 1.75; white-space: pre-wrap;
}
.sd-prompt-actions { display: flex; gap: 8px; }
.sd-prompt-actions button {
  min-height: 34px; padding: 0 14px; border: 1px solid #e6dcc4; border-radius: 9px;
  background: #fff; color: #6b5220; font: inherit; font-size: 11.5px; font-weight: 800; cursor: pointer;
}
.sd-prompt-actions button.primary { border: 0; background: linear-gradient(135deg, #c8872e, #e0a94a); color: #fff; }
.sd-prompt-actions button.danger { border-color: #edc9c2; color: #b44c43; }
.sd-prompt-actions button:disabled { opacity: .5; cursor: not-allowed; }
.sd-learn-block > header .primary {
  margin-left: auto; min-height: 36px; padding: 0 16px; border: 0; border-radius: 10px;
  background: linear-gradient(135deg, #c8872e, #e0a94a); color: #fff; font: inherit; font-size: 12px; font-weight: 800; cursor: pointer;
}

.sd-prompt > header em.sd-prompt-group {
  margin-left: auto; padding: 2px 8px; border-radius: 999px;
  background: #eef4f4; color: #607a7e; font-size: 10.5px; font-style: normal; font-weight: 800;
}

/* ---- 需求体检：新增板块 ---- */
.sd-howto { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-top: 14px; }
.sd-howto span {
  display: grid; grid-template-columns: 24px minmax(0, 1fr); gap: 3px 9px; align-items: center;
  padding: 11px 13px; border: 1px solid #e7eef0; border-radius: 12px; background: #fbfdfd;
}
.sd-howto em {
  grid-row: span 2; width: 24px; height: 24px; display: grid; place-items: center; border-radius: 50%;
  background: linear-gradient(135deg, #1c837a, #12655f); color: #fff; font-size: 11px; font-style: normal; font-weight: 800;
}
.sd-howto b { color: #1d3238; font-size: 13px; }
.sd-howto small { color: #7b9096; font-size: 11.5px; line-height: 1.5; }



/* 顶部模式切换收紧 */
.sd-modes button { padding: 11px 15px; }
.sd-modes button b { font-size: 13.5px; }
.sd-modes button small { font-size: 11.5px; }

@media (max-width: 900px) {
  .sd-howto { grid-template-columns: minmax(0, 1fr); }
}

/* ---- 托管运行：首字图标 + 卡片打磨 ---- */
.sd-host-mark {
  flex: none; width: 42px; height: 42px; display: grid; place-items: center; border-radius: 12px;
  font-size: 17px; font-weight: 800; letter-spacing: 0; border: 1px solid transparent;
}
.sd-host-mark.tone-teal { background: #e9f4f2; color: #16766f; border-color: #d5eae6; }
.sd-host-mark.tone-blue { background: #eaf1f8; color: #3979b8; border-color: #dbe7f2; }
.sd-host-mark.tone-amber { background: #fdf3e2; color: #b0741f; border-color: #f2e2c6; }
.sd-host-mark.tone-violet { background: #f1eefa; color: #6b53a8; border-color: #e3ddf4; }
.sd-host-mark.tone-green { background: #e9f4ec; color: #2f7d4f; border-color: #d9e8dc; }
.sd-host-mark.tone-coral { background: #fbeeea; color: #c2563f; border-color: #f2dbd4; }

.sd-host-head { gap: 13px; }
.sd-host-info > b { font-size: 14px; }
.sd-host-right em { padding: 3px 10px; border-radius: 999px; font-size: 11px; }

/* 趋势柱：带数值标签 */
.sd-bars { display: flex; align-items: flex-end; gap: 8px; height: 96px; }
.sd-bars span { flex: 1; display: grid; align-content: end; justify-items: center; gap: 5px; height: 100%; }
.sd-bars span i { width: 100%; border-radius: 7px 7px 3px 3px; background: linear-gradient(180deg, #2f9a90, #1c837a); }
.sd-bars span.low i { background: linear-gradient(180deg, #e0a94a, #c8872e); }
.sd-bars span em { color: #8fa2a8; font-size: 10.5px; font-style: normal; font-weight: 700; }
.sd-bars span.low em { color: #b0741f; }

/* 趋势柱修正：柱体撑满各自轨道，标签单独一行 */
.sd-bars { display: flex; align-items: flex-end; gap: 8px; height: 88px; }
.sd-bars span { flex: 1; height: 100%; display: flex; align-items: flex-end; }
.sd-bars span i {
  width: 100%; flex: none; border-radius: 7px 7px 3px 3px;
  background: linear-gradient(180deg, #2f9a90, #1c837a);
}
.sd-bars span.low i { background: linear-gradient(180deg, #e0a94a, #c8872e); }
.sd-bar-axis { display: flex; gap: 8px; margin-top: 6px; }
.sd-bar-axis em { flex: 1; text-align: center; color: #8fa2a8; font-size: 10.5px; font-style: normal; font-weight: 700; }
.sd-bar-axis em.low { color: #b0741f; }

/* ---- 服务台：不用装饰图，改用数字徽标与色块 ---- */
.sd-guide-hero { padding: 18px 20px; border-left: 4px solid #1c837a; border-radius: 12px; background: linear-gradient(135deg, #f4faf9, #f7fbfb); }
.sd-guide-hero > div { display: grid; gap: 6px; }
.sd-guide-hero b { color: #1d3238; font-size: 16px; }
.sd-guide-hero small { color: #6d8489; font-size: 12.5px; }

.sd-form-head { display: grid; grid-template-columns: 44px minmax(0, 1fr); gap: 14px; align-items: start; }
.sd-step-no {
  width: 44px; height: 44px; display: grid; place-items: center; border-radius: 13px;
  background: linear-gradient(135deg, #1c837a, #12655f); color: #fff;
  font-size: 19px; font-weight: 800; box-shadow: 0 8px 18px rgba(18,101,95,.2);
}

/* ---- 提示词：筛选条 + 卡片重做 ---- */
.sd-prompt-filter { display: flex; flex-wrap: wrap; gap: 7px; }
.sd-prompt-filter button {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 6px 13px; border: 1px solid #e6ecec; border-radius: 999px;
  background: #fff; color: #5a7076; font: inherit; font-size: 11.5px; font-weight: 800; cursor: pointer;
  transition: border-color .16s ease, background .16s ease, color .16s ease;
}
.sd-prompt-filter button:hover { border-color: rgba(22,118,111,.4); color: var(--teal-dark, #0f5854); }
.sd-prompt-filter button.on { border-color: transparent; background: linear-gradient(135deg, #1c837a, #12655f); color: #fff; }
.sd-prompt-filter button em {
  padding: 0 5px; border-radius: 999px; background: rgba(0,0,0,.07);
  font-size: 10px; font-style: normal; font-weight: 800;
}
.sd-prompt-filter button.on em { background: rgba(255,255,255,.24); }

.sd-prompt-grid { grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 12px; }
.sd-prompt {
  grid-template-rows: auto auto minmax(0, 1fr) auto;
  gap: 9px; padding: 15px 16px; border-radius: 13px;
  transition: border-color .18s ease, box-shadow .18s ease, transform .18s ease;
}
.sd-prompt:hover { border-color: rgba(22,118,111,.32); box-shadow: 0 10px 24px rgba(24,60,68,.06); transform: translateY(-1px); }
.sd-prompt > header { align-items: baseline; }
.sd-prompt > header b { font-size: 13.5px; color: #1d3238; }
.sd-prompt > header em.sd-prompt-group { background: #eef4f4; color: #5f7a7e; }
.sd-prompt-desc { color: #7b9096; font-size: 11.5px; line-height: 1.6; }
.sd-prompt-text {
  max-height: 96px; overflow: auto; padding: 10px 12px; border-radius: 10px;
  border: 1px solid #eef2f2; background: #f8fbfb; color: #4d656c;
  font-size: 11.5px; line-height: 1.75;
  scrollbar-width: thin; scrollbar-color: #cfe0dd transparent;
}
.sd-prompt-text::-webkit-scrollbar { width: 6px; }
.sd-prompt-text::-webkit-scrollbar-thumb { border-radius: 999px; background: #cfe0dd; }
.sd-prompt-actions { margin-top: 2px; }
.sd-prompt-actions button {
  border-color: #e2ecee; color: #4d656c; border-radius: 8px;
}
.sd-prompt-actions button:hover { border-color: rgba(22,118,111,.4); color: var(--teal-dark, #0f5854); }
.sd-prompt-actions button.primary { background: linear-gradient(135deg, #1c837a, #12655f); border: 0; }
.sd-prompt.custom { border-color: #d9e8e6; background: linear-gradient(180deg, #fbfdfd, #ffffff); }

/* ---- 提示词优化：弹窗与标记 ---- */
.sd-prompt > header em.sd-prompt-optimized {
  padding: 2px 8px; border-radius: 999px;
  background: #e9f4f2; color: #16766f; font-size: 10.5px; font-style: normal; font-weight: 800;
}
.sd-prompt-actions button.optimize { border-color: rgba(22,118,111,.34); color: var(--teal-dark, #0f5854); }

.sd-modal {
  position: fixed; inset: 0; z-index: 60; display: grid; place-items: center; padding: 24px;
  background: rgba(20, 38, 40, .38); backdrop-filter: blur(2px);
}
.sd-modal-box {
  width: min(640px, 100%); max-height: 82vh; overflow: auto;
  display: grid; gap: 14px; padding: 20px 22px;
  border-radius: 16px; background: #fff; box-shadow: 0 30px 70px rgba(15, 40, 44, .3);
}
.sd-modal-box > header { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; }
.sd-modal-box > header b { display: block; margin: 2px 0 4px; color: #1d3238; font-size: 16px; }
.sd-modal-box > header small { color: #7b9096; font-size: 12px; line-height: 1.6; }
.sd-modal-close {
  flex: none; width: 30px; height: 30px; display: grid; place-items: center;
  border: 1px solid #e2ecee; border-radius: 9px; background: #fff; color: #6d8489;
  font-size: 13px; cursor: pointer; transition: border-color .16s, color .16s;
}
.sd-modal-close:hover { border-color: rgba(22,118,111,.4); color: var(--teal-dark, #0f5854); }
.sd-modal-box textarea {
  width: 100%; min-height: 220px; padding: 14px 15px; resize: vertical;
  border: 1px solid #dfeae8; border-radius: 12px; background: #fbfdfd;
  color: #33494e; font: inherit; font-size: 13px; line-height: 1.85; outline: 0;
}
.sd-modal-box textarea:focus { border-color: #75aaa5; background: #fff; box-shadow: 0 0 0 3px rgba(22,118,111,.1); }
.sd-modal-foot { display: flex; align-items: center; justify-content: space-between; gap: 14px; }
.sd-modal-foot > small { color: #8fa2a8; font-size: 11.5px; }
.sd-modal-foot > div { display: flex; gap: 8px; }
.sd-modal-foot button {
  min-height: 36px; padding: 0 16px; border: 1px solid #e2ecee; border-radius: 9px;
  background: #fff; color: #4d656c; font: inherit; font-size: 12px; font-weight: 800; cursor: pointer;
}
.sd-modal-foot button:hover { border-color: rgba(22,118,111,.4); color: var(--teal-dark, #0f5854); }
.sd-modal-foot button.primary { border: 0; background: linear-gradient(135deg, #1c837a, #12655f); color: #fff; }
.sd-modal-foot button:disabled { opacity: .5; cursor: not-allowed; }

/* ---- 自由描述：多轮对话布局收紧 ---- */
.sd-chat { display: grid; grid-template-rows: auto auto minmax(0, 1fr) auto; gap: 12px; }
.sd-thread { max-width: 960px; width: 100%; margin: 0 auto; }

.sd-facts {
  display: flex; flex-wrap: wrap; align-items: center; gap: 8px;
  max-width: 960px; width: 100%; margin: 0 auto;
  padding: 10px 14px; border: 1px solid #e7eef0; border-radius: 12px; background: #fbfdfd;
}
.sd-facts > small { color: #93a3a7; font-size: 11.5px; font-weight: 800; }
.sd-facts > span {
  padding: 4px 11px; border-radius: 999px; border: 1px solid #e6ecec;
  background: #fff; color: #9aacb0; font-size: 11.5px; font-weight: 800;
}
.sd-facts > span.on { border-color: transparent; background: #e9f4f2; color: #16766f; }
.sd-facts > em {
  margin-left: auto; max-width: 46%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  color: #5a7076; font-size: 11.5px; font-style: normal;
}

.sd-replies { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 10px; }
.sd-replies button {
  padding: 7px 14px; border: 1px solid #dcebe8; border-radius: 999px;
  background: #fff; color: #1f6b64; font: inherit; font-size: 12px; font-weight: 800; cursor: pointer;
  transition: border-color .16s ease, background .16s ease, transform .16s ease;
}
.sd-replies button:hover { border-color: rgba(22,118,111,.5); background: #f2faf8; transform: translateY(-1px); }
.sd-replies button:disabled { opacity: .5; cursor: not-allowed; }

.sd-msg { max-width: 100%; }
.sd-bubble { max-width: 660px; }
.sd-input { max-width: 960px; width: 100%; margin: 0 auto; }

/* ---- 分步引导：放大字号、按钮与间距，比例更均衡 ---- */
.sd-guided { display: grid; gap: 18px; max-width: 1180px; margin: 0 auto; }

.sd-guide-hero { padding: 22px 26px; border-left: 5px solid #1c837a; }
.sd-guide-hero b { font-size: 20px; letter-spacing: -.01em; }
.sd-guide-hero small { font-size: 14px; }

.sd-howto { gap: 14px; margin-top: 0; }
.sd-howto span { grid-template-columns: 32px minmax(0, 1fr); gap: 4px 12px; padding: 15px 18px; border-radius: 14px; }
.sd-howto em { width: 32px; height: 32px; font-size: 14px; }
.sd-howto b { font-size: 15px; }
.sd-howto small { font-size: 13px; }

.sd-steps { gap: 10px; }
.sd-steps span { gap: 8px; padding: 9px 18px; font-size: 13.5px; }
.sd-steps span em { width: 22px; height: 22px; font-size: 12px; }

.sd-form { gap: 20px; padding: 28px 30px; border-radius: 18px; }
.sd-form-head { grid-template-columns: 56px minmax(0, 1fr); gap: 18px; }
.sd-step-no { width: 56px; height: 56px; border-radius: 16px; font-size: 24px; }
.sd-form-headcopy { gap: 8px; }
.sd-form-headcopy h3 { font-size: 23px; }
.sd-hint { font-size: 14px; }
.sd-why { font-size: 13.5px; line-height: 1.75; }

.sd-chips { gap: 12px; }
.sd-chips.wide { grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
.sd-chips button {
  padding: 15px 20px; border-radius: 14px; font-size: 15px; font-weight: 700; gap: 4px;
  transition: border-color .16s ease, background .16s ease, transform .16s ease, box-shadow .16s ease;
}
.sd-chips button:hover { border-color: rgba(22,118,111,.45); transform: translateY(-1px); box-shadow: 0 8px 18px rgba(24,60,68,.06); }
.sd-chips button em { font-size: 12.5px; }
.sd-chips button.on { border-color: #1c837a; background: #f2faf8; color: #12655f; }
.sd-note { font-size: 13.5px; }
.sd-note input { padding: 13px 16px; font-size: 14px; }

.sd-form-foot { padding-top: 8px; }
.sd-form-foot button {
  min-width: 132px; min-height: 50px; padding: 0 28px; border-radius: 13px; font-size: 15px;
}
.sd-form-foot button.primary { box-shadow: 0 10px 22px rgba(18,101,95,.22); }
.sd-progress { font-size: 14px; }

/* 报告区同步放大 */
.sd-report { display: grid; gap: 18px; }
.sd-verdict { padding: 24px 28px; border-radius: 16px; }
.sd-verdict h3 { font-size: 24px; }
.sd-verdict p { font-size: 14px; line-height: 1.8; }
.sd-verdict button { min-height: 44px; padding: 0 22px; font-size: 14px; border-radius: 11px; }
.sd-report-card { padding: 24px 26px; border-radius: 16px; }
.sd-report-card header b { font-size: 19px; }
.sd-report-card header small { font-size: 13.5px; }
.sd-dims span small, .sd-dims span em { font-size: 13px; }
.sd-roi span small { font-size: 12.5px; }
.sd-roi span b { font-size: 19px; }
.sd-report-actions button { min-height: 46px; padding: 0 24px; font-size: 14px; border-radius: 12px; }
</style>
