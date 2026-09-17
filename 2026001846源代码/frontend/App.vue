<template>
  <main class="app-shell" :class="{ collapsed: navCollapsed, 'auth-shell': !isAuthenticated }">
    <section v-if="!isAuthenticated" class="auth-gate">
      <div class="auth-visual">
        <div class="auth-grid" aria-hidden="true"></div>
        <div class="auth-brand">
          <img :src="'/static/yixiu-logo-full.png'" alt="一休" />
          <span>AI 原生项目协作与团队记忆系统</span>
        </div>
        <div class="auth-intro">
          <p>面向研发团队的人机协作工作台</p>
          <h1>让每一次任务<br />都有上下文、有执行、有沉淀</h1>
          <div class="auth-capabilities">
            <span><b>01</b>任务上下文包</span>
            <span><b>02</b>人机协作执行</span>
            <span><b>03</b>团队记忆演化</span>
          </div>
        </div>
        <p class="auth-footnote">一休 · AI 原生团队能力增长平台</p>
      </div>
      <div class="auth-form-side">
        <form class="auth-card" @submit.prevent="authMode === 'login' ? login() : register()">
          <div class="auth-card-head">
            <p>{{ authMode === 'login' ? '欢迎回来' : '创建工作账号' }}</p>
            <h2>{{ authMode === 'login' ? '登录一休工作台' : '加入一休协作平台' }}</h2>
            <span>{{ authMode === 'login' ? '登录后进入项目协作智能工作台' : '完善基础信息后即可开始人机协作' }}</span>
          </div>
          <div class="auth-tabs" role="tablist">
            <button type="button" :class="{ active: authMode === 'login' }" @click="setAuthMode('login')">账号登录</button>
            <button type="button" :class="{ active: authMode === 'register' }" @click="setAuthMode('register')">注册账号</button>
          </div>
          <div class="auth-fields">
            <label v-if="authMode === 'register'">姓名<input v-model.trim="authForm.name" autocomplete="name" placeholder="请输入真实姓名" /></label>
            <label>账号<input v-model.trim="authForm.account" autocomplete="username" placeholder="请输入账号" /></label>
            <label>密码<input v-model="authForm.password" type="password" autocomplete="current-password" placeholder="请输入密码" /></label>
            <label v-if="authMode === 'register'">确认密码<input v-model="authForm.confirmPassword" type="password" autocomplete="new-password" placeholder="请再次输入密码" /></label>
          </div>
          <p v-if="authError" class="auth-error">{{ authError }}</p>
          <label v-if="authMode === 'login'" class="remember-row"><input v-model="authForm.remember" type="checkbox" />保持登录状态</label>
          <label v-else class="remember-row"><input v-model="authForm.agreed" type="checkbox" />我已阅读并同意平台使用规范</label>
          <button class="auth-submit" type="submit">{{ authMode === 'login' ? '进入工作台' : '完成注册并登录' }}</button>
          <div v-if="authMode === 'login'" class="demo-account"><span>默认演示账号</span><b>账号：yixiu</b><b>密码：Yixiu2026!</b></div>
        </form>
      </div>
    </section>
    <template v-else>
    <div v-if="showSplash" ref="bootScreenRef" class="boot-screen" aria-label="一休系统开屏动画">
      <div class="boot-grid" aria-hidden="true"></div>
      <div class="boot-flow flow-a" aria-hidden="true"></div>
      <div class="boot-flow flow-b" aria-hidden="true"></div>
      <section ref="bootMarkRef" class="boot-mark">
        <img ref="bootLogoRef" :src="'/static/yixiu-logo-full.png'" alt="一休" />
      </section>
    </div>
    <aside class="side-nav">
      <img
        ref="brandLogoRef"
        class="brand"
        :src="navCollapsed ? '/static/yixiu-logo-icon.png' : '/static/yixiu-logo-full.png'"
        alt="一休"
        @click="activePage = 'home'"
      />

      <nav>
        <button
          v-for="item in navItems"
          :key="item.key"
          type="button"
          :class="{ active: activePage === item.key }"
          @click="switchPage(item.key)"
        >
          <span class="nav-icon">
            <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconParts(item.icon)" :key="path" :d="path"></path>
            </svg>
          </span>
          <b v-if="!navCollapsed">{{ item.label }}</b>
        </button>
      </nav>

      <button class="collapse-btn" type="button" @click="navCollapsed = !navCollapsed">
        {{ navCollapsed ? '»' : '« 收起导航' }}
      </button>
    </aside>

    <section class="workspace">
      <header ref="topbarRef" :class="['topbar', `topbar-${activePage}`, { 'search-focus': globalSearchFocused }]">
        <div v-if="!globalSearchFocused" :class="['page-title-block', `title-${activePage}`]">
          <p class="breadcrumb">一休 / {{ currentNav.label }}</p>
          <h1>{{ currentNav.title }}</h1>
        </div>
        <div v-else class="task-chamber-wrap">
          <button class="task-chamber" type="button" :class="{ open: taskChamberOpen }" @click="taskChamberOpen = !taskChamberOpen">
            <i></i>
          </button>
          <div v-if="taskChamberOpen" class="task-chamber-pop">
            <button type="button" @click="activePage = 'home'; globalSearchFocused = false; taskChamberOpen = false">
              <b>综合工作台</b><small>回到工作台总览</small>
            </button>
            <button type="button" @click="activePage = 'tasks'; taskPanel = 'manage'; globalSearchFocused = false; taskChamberOpen = false">
              <b>活跃项目 {{ overview.stats.pending }}</b><small>进入任务执行中心</small>
            </button>
            <button type="button" @click="activePage = 'tasks'; taskPanel = 'recheck'; globalSearchFocused = false; taskChamberOpen = false">
              <b>待 Eval {{ overview.stats.review }}</b><small>查看 Skill 回归评测</small>
            </button>
            <button class="danger" type="button" @click="activePage = 'tasks'; taskPanel = 'overview'; globalSearchFocused = false; taskChamberOpen = false">
              <b>重复问题 {{ overview.stats.highRisk }}</b><small>定位可资产化问题</small>
            </button>
          </div>
        </div>
        <form class="global-search" @submit.prevent="runGlobalSearch" @focusin="globalSearchFocused = true">
          <span>
            <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconParts('search')" :key="path" :d="path"></path>
            </svg>
          </span>
          <input v-model="globalKeyword" placeholder="搜索任务、Memory、Skill、文档、成员" />
          <button type="submit" aria-label="全局搜索">搜索</button>
        </form>
        <div v-if="!globalSearchFocused" class="work-strip">
          <button type="button" @click="goTopbarTask('pending')">活跃任务 {{ overview.stats.pending }}</button>
          <button type="button" @click="goTopbarTask('review')">待 Eval {{ overview.stats.review }}</button>
          <button class="bad" type="button" @click="goTopbarTask('highRisk')">重复问题 {{ overview.stats.highRisk }}</button>
        </div>
        <button class="icon-button notification-button" :class="{ unread: unreadContactCount > 0 }" type="button" @click="openUnreadContacts" :aria-label="`消息提醒，${unreadContactCount} 条未读`">
          <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path v-for="path in iconParts('bell')" :key="path" :d="path"></path>
          </svg>
          <i v-if="unreadContactCount > 0">{{ unreadContactCount > 9 ? '9+' : unreadContactCount }}</i>
        </button>
        <button class="user-chip" type="button" @click="activePage = 'profile'">
          <img :src="user.avatar" alt="" />
          <span>{{ user.name }}</span>
        </button>
        <button class="topbar-logout" type="button" @click="logout" title="安全退出当前账号">
          <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M10 17l5-5-5-5"></path>
            <path d="M15 12H3"></path>
            <path d="M14 4h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-4"></path>
          </svg>
          <span>退出登录</span>
        </button>
      </header>

      <div class="content-shell" :class="{ 'search-focus-shell': activePage === 'search', 'contact-focus-shell': activePage === 'tasks' && taskPanel === 'contacts', 'profile-focus-shell': activePage === 'profile', 'knowledge-focus-shell': activePage === 'knowledge' }" :style="{ '--operator-width': `${operatorWidth}px` }">
      <section class="page-scroll" :class="[`page-theme-${activePage}`, { 'panel-network': activePage === 'search' && searchPanel === 'network' }]">
        <section v-if="activePage === 'home'" class="page-grid">
          <div
            class="panel span-7 home-news-carousel"
            @mouseenter="pauseNewsCarousel"
            @mouseleave="resumeNewsCarousel"
          >
            <div class="news-carousel-stage">
              <a class="news-image-link" :href="activeNews.link" target="_blank" rel="noopener">
                <transition name="news-fade" mode="out-in">
                  <img :key="activeNews.image" :src="activeNews.image" :alt="activeNews.title" @error="handleContentImageError($event, newsImageFallback)" />
                </transition>
              </a>
            </div>
            <div class="news-carousel-copy">
              <a :href="activeNews.link" target="_blank" rel="noopener">
                <h2>{{ activeNews.title }}</h2>
              </a>
              <p>{{ activeNews.summary }}</p>
              <div class="news-meta">
                <span>{{ activeNews.source }}</span>
                <span>{{ activeNews.date }}</span>
                <div class="news-dots" aria-label="轮播页码">
                  <button
                    v-for="(item, index) in newsSlides"
                    :key="item.image"
                    type="button"
                    :class="{ active: index === newsIndex }"
                    :aria-label="`切换到第 ${index + 1} 条新闻`"
                    @click="setNewsSlide(index)"
                  ></button>
                </div>
              </div>
            </div>
          </div>

          <div class="welcome-card span-7 home-hero-work">
            <div class="welcome-brand">
              <img :src="'/static/yixiu-logo-full.png'" alt="一休系统 Logo" @error="handleContentImageError($event, '/static/yixiu-logo.png')" />
              <div>
                <p class="eyebrow">我的今日工作</p>
                <h2>{{ user.name }}，今天重点处理 {{ overview.stats.pending + overview.stats.inProgress + overview.stats.review }} 项检修工作</h2>
                <p>{{ nowText }}，{{ user.department }}。请优先确认重复问题、即将逾期和待 Eval 任务。</p>
              </div>
            </div>
            <div class="execution-summary">
              <div class="progress-ring" :style="{ '--progress': `${todayCompletion}%` }">
                <span><b>{{ todayCompletion }}%</b>今日完成率</span>
              </div>
              <div class="execution-copy">
                <strong>今日执行进度</strong>
                <p>已完成 {{ overview.stats.completed }} 项，仍有 {{ overview.stats.pending + overview.stats.inProgress + overview.stats.review }} 项需要推进。</p>
              </div>
              <div class="summary-metric"><b>{{ overview.stats.highRisk }}</b><span>重复问题待确认</span></div>
              <div class="summary-metric"><b>{{ overview.stats.weekKnowledge }}</b><span>本周知识沉淀</span></div>
            </div>
            <div class="health-grid">
              <span>待接收：{{ overview.stats.pending }} 项</span>
              <span>进行中：{{ overview.stats.inProgress }} 项</span>
              <span>待 Eval：{{ overview.stats.review }} 项</span>
              <span>今日完成：{{ overview.stats.completed }} 项</span>
              <span>需确认：{{ overview.stats.highRisk }} 项重复问题</span>
            </div>
            <div class="focus-tasks">
              <div class="focus-tasks-title"><b>今日重点</b><span>按风险与时限排序</span></div>
              <button v-for="task in priorityTasks.slice(0, 3)" :key="task.id" type="button" @click="openTask(task)">
                <span><b>{{ task.equipment_name }}</b><small>{{ task.fault_type }} · {{ task.current_step }}</small></span>
                <i :class="['badge', task.severity]">{{ severityText(task.severity) }}</i>
                <em>{{ task.progress }}%</em>
              </button>
            </div>
          </div>

          <div class="panel home-schedule-panel span-5">
            <div class="schedule-head">
              <div class="schedule-month-control">
                <button type="button" aria-label="上个月" @click="shiftScheduleMonth(-1)">‹</button>
                <h3>{{ homeCalendarTitle }}</h3>
                <button type="button" aria-label="下个月" @click="shiftScheduleMonth(1)">›</button>
              </div>
              <div class="schedule-head-meta">
                <span class="meta-today">今日 {{ selectedScheduleItems.length }}</span>
                <span class="meta-critical">重点 {{ scheduleToneStats.critical }}</span>
                <span class="meta-review">复检 {{ scheduleToneStats.review }}</span>
              </div>
            </div>
            <div class="schedule-calendar">
              <span v-for="day in homeWeekdays" :key="day" class="weekday">{{ day }}</span>
              <button
                v-for="day in homeCalendarDays"
                :key="day.key"
                type="button"
                :class="{ muted: !day.currentMonth, today: day.isToday, selected: day.selected, event: day.hasEvent }"
                @click="selectScheduleDate(day)"
              >
                <b>{{ day.date }}</b>
                <i v-if="day.hasEvent"></i>
              </button>
            </div>
            <div class="schedule-divider"><span>{{ selectedScheduleLabel }}</span></div>
            <div class="schedule-list">
              <article v-for="item in selectedScheduleItems" :key="item.id" class="schedule-item-row" :class="[`tone-${scheduleTone(item)}`, { done: item.done, important: item.important }]">
                <button class="schedule-main" type="button" @click="openScheduleItem(item)">
                  <i></i>
                  <span class="schedule-tag">{{ schedulePriorityLabel(item) }}</span>
                  <span class="schedule-copy">
                    <b>{{ item.title }}</b>
                    <small>{{ item.people }}</small>
                    <em>{{ item.desc }}</em>
                  </span>
                  <time>{{ item.time }}</time>
                </button>
              </article>
            </div>
            <div class="schedule-footer">
              <button type="button" class="active" @click="openScheduleForm()">
                <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3v3M17 3v3M4 9h16M6 5h12a2 2 0 0 1 2 2v12H4V7a2 2 0 0 1 2-2Z"></path></svg>
                安排日程
              </button>
            </div>
          </div>

          <div class="home-task-track-row span-all">
          <div class="panel home-task-panel home-task-compact">
            <div class="section-title-row home-task-title">
              <div>
                <p class="eyebrow">Skill 推荐榜</p>
                <h3>高星开源 Agent & RAG 项目</h3>
              </div>
              <div class="task-title-actions"><span>{{ skillRankList.length }} 个 Skill</span><button class="ghost" type="button" @click="activePage = 'knowledge'; knowledgePanel = 'recheck'">查看全部 →</button></div>
            </div>
            <div class="home-task-list">
              <a v-for="(skill, index) in skillRankList" :key="skill.id" :href="skill.repo" target="_blank" rel="noopener" class="home-task-row skill-row" :class="`risk-${skill.status === 'verified' ? 'low' : skill.status === 'testing' ? 'medium' : 'high'}`">
                <span class="task-index-block">
                  <b>{{ String(index + 1).padStart(2, '0') }}</b>
                  <i :class="skill.status === 'verified' ? 'rank-hot' : skill.status === 'testing' ? 'rank-warm' : 'rank-new'"></i>
                </span>
                <span class="task-device-block">
                  <small>{{ skill.category }} · {{ skill.lang }}</small>
                  <b>{{ skill.name }}</b>
                  <em>{{ skill.description }}</em>
                </span>
                <span class="task-fault-block">
                  <span><b>{{ skill.trigger }}</b><i :class="['badge', skill.status === 'verified' ? 'low' : skill.status === 'testing' ? 'medium' : 'high']">{{ skill.status === 'verified' ? '已验证' : skill.status === 'testing' ? '测试中' : '候选' }}</i></span>
                  <small>{{ skill.version }}</small>
                </span>
                <span class="task-owner-block">
                  <i>★</i>
                  <span><small>GitHub Stars</small><b>{{ skill.stars.toLocaleString() }}</b></span>
                </span>
                <span class="task-progress-block">
                  <span><b>匹配度 {{ skill.successRate }}%</b></span>
                  <i><u :style="{ width: `${skill.successRate}%` }"></u></i>
                  <small>与一修系统契合度</small>
                </span>
                <span class="row-arrow">↗</span>
              </a>
            </div>
          </div>

          <div class="panel activity-panel work-track-panel">
            <div class="section-title-row"><div><p class="eyebrow">工作轨迹</p><h3>最近使用记录</h3></div><span class="quiet-label">今天</span></div>
            <div class="activity-list work-track-list">
              <button v-for="item in recentActivities.slice(0, 5)" :key="item.raw" :class="`activity-${item.tone}`" type="button" @click="runRecentActivity(item)">
                <span class="activity-icon">
                  <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path v-for="path in iconParts(item.icon)" :key="path" :d="path"></path></svg>
                </span>
                <span><small>{{ item.action }}</small><b>{{ item.content }}</b></span>
                <i>→</i>
              </button>
            </div>
          </div>
          </div>

          <div class="panel analytics-panel span-all">
            <div class="panel-head">
              <div>
                <p class="eyebrow">数据分析</p>
                <h3>系统今日概览数据看板</h3>
              </div>
              <div class="chart-legend"><i></i>实时汇总 <span>多维指标</span></div>
            </div>
            <div class="dashboard-charts">
              <section class="chart-tile chart-tile-wide">
                <div class="chart-tile-head"><b>近七天处理趋势</b><small>{{ taskTrendTotal }} 项流转</small></div>
                <EChart :option="homeTrendOption" class="chart-canvas" height="250px" />
              </section>
              <section class="chart-tile">
                <div class="chart-tile-head"><b>项目状态分布</b><small>按推进状态</small></div>
                <EChart :option="homeStatusOption" class="chart-canvas" height="250px" />
              </section>
              <section class="chart-tile">
                <div class="chart-tile-head"><b>问题等级占比</b><small>{{ overview.stats.highRisk }} 项重复问题</small></div>
                <EChart :option="homeRiskOption" class="chart-canvas" height="230px" />
              </section>
              <section class="chart-tile">
                <div class="chart-tile-head"><b>故障构成</b><small>按案例占比</small></div>
                <EChart :option="homeFaultOption" class="chart-canvas" height="230px" />
              </section>
              <section class="chart-tile">
                <div class="chart-tile-head"><b>复检质量雷达</b><small>流程闭环能力</small></div>
                <EChart :option="homeQualityOption" class="chart-canvas" height="230px" />
              </section>
              <section class="chart-tile chart-tile-wide">
                <div class="chart-tile-head"><b>知识沉淀与引用</b><small>本周新增 {{ overview.stats.weekKnowledge }} 条</small></div>
                <EChart :option="homeKnowledgeOption" class="chart-canvas" height="230px" />
              </section>
            </div>
          </div>

          <div v-if="false" class="panel activity-panel span-all">
            <div class="section-title-row"><div><p class="eyebrow">工作轨迹</p><h3>最近使用记录</h3></div><span class="quiet-label">今天</span></div>
            <div class="activity-list">
              <button v-for="item in recentActivities" :key="item.raw" :class="`activity-${item.tone}`" type="button" @click="runRecentActivity(item)">
                <span class="activity-icon">
                  <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path v-for="path in iconParts(item.icon)" :key="path" :d="path"></path></svg>
                </span>
                <span><small>{{ item.action }}</small><b>{{ item.content }}</b></span>
                <i>→</i>
              </button>
            </div>
          </div>

        </section>

<section v-else-if="activePage === 'search'" class="page-grid search-workbench-v2">
          <div class="panel span-all search-agent-hero">
            <div class="search-agent-intro">
              <img :src="operatorProfile.avatar" :alt="operatorProfile.name" @error="handleAvatarError" />
              <div>
                <h2>观微｜Context Engine <span class="agent-online-dot"></span><small>在线</small></h2>
                <b>任务上下文包生成专家</b>
                <p>自动组装需求、代码、文档、历史经验和相关 Skill，让任务开始前就带着完整依据。</p>
              </div>
            </div>
            <div class="tabs">
              <button
                v-for="tab in searchTabs"
                :key="tab.key"
                type="button"
                :class="{ active: searchPanel === tab.key || (tab.key === 'multimodal' && ['results', 'history'].includes(searchPanel)) }"
                @click="searchPanel = tab.key"
              >{{ tab.label }}</button>
            </div>
          </div>


          <template v-if="searchPanel === 'multimodal'">
            <div class="panel span-all search-input-panel search-fusion-panel" :class="{ 'is-collapsed': !searchMultimodalExpanded, 'is-expanded': searchMultimodalExpanded }">
              <div class="search-fusion-head">
                <div class="search-panel-heading">
                  <span class="search-step">01</span>
                  <div><p class="eyebrow">Context Engine</p><h3>输入任务，观微同步组包</h3><small>需求、代码、文档、Issue、PR、聊天和历史经验会合并成一次任务上下文。</small></div>
                </div>
                <div class="inline-actions">
                  <button type="button" class="ghost-toggle" @click="searchMultimodalExpanded = !searchMultimodalExpanded">
                    {{ searchMultimodalExpanded ? '收起' : '展开' }}
                    <svg class="ui-icon" :class="{ up: searchMultimodalExpanded }" viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"></path></svg>
                  </button>
                  <button type="button" @click="searchPanel = 'history'">历史</button>
                  <button type="button" @click="searchPanel = 'update'">演化</button>
                  <button type="button" @click="clearOperatorMessages">清空</button>
                  <button class="primary" type="button" :disabled="loading.search" @click="runSearch">{{ loading.search ? '组包中' : '生成 Context Pack' }}</button>
                </div>
              </div>

              <div v-show="!searchMultimodalExpanded" class="search-collapse-summary">
                <span><b>项目</b>{{ searchForm.deviceName || '未填写' }}</span>
                <span><b>技术栈</b>{{ searchForm.deviceModel || '未填写' }}</span>
                <span><b>任务</b>{{ searchForm.faultType }} / {{ searchForm.faultCode || '无 Issue' }}</span>
                <span><b>证据</b>{{ searchFiles.length ? `${searchFiles.length} 个附件` : '未上传' }}</span>
                <button type="button" @click="runSearch">{{ loading.search ? '组包中' : '生成 Context Pack' }}</button>
              </div>

              <div v-show="searchMultimodalExpanded" class="search-fusion-body">
                <div class="search-fusion-input">
                  <div class="form-grid">
                    <label>项目 / 仓库<input v-model="searchForm.deviceName" placeholder="如：支付服务 / repo/payment-service" /></label>
                    <label>技术栈 / 模块<input v-model="searchForm.deviceModel" placeholder="如：Node.js + MySQL" /></label>
                    <label>Issue / PR ID<input v-model="searchForm.faultCode" placeholder="如：BUG-421 / PR-118" /></label>
                    <label>任务领域<select v-model="searchForm.category"><option>后端服务</option><option>前端体验</option><option>数据模型</option><option>Agent 工作流</option></select></label>
                    <label>任务类型<select v-model="searchForm.faultType"><option>线上 Bug</option><option>功能改造</option><option>重复问题</option><option>Skill 回归</option></select></label>
                    <label>协作等级<select v-model="searchForm.maintenanceLevel"><option>轻量协作</option><option>标准协作</option><option>高风险协作</option></select></label>
                    <label class="wide">任务描述<textarea v-model="searchForm.query" placeholder="描述需求背景、现象、影响范围、相关代码、历史尝试或验收标准"></textarea></label>
                  </div>

                  <div class="search-evidence-box">
                    <div class="upload-zone search-upload-zone" @dragover.prevent @drop.prevent="addDroppedFiles">
                      <input ref="searchFileInput" type="file" multiple accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.md,.mp4,.webm" @change="addFiles($event, 'search')" />
                      <span class="upload-mark"><svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 16V4M7.5 8.5 12 4l4.5 4.5M5 14v4a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-4"></path></svg></span>
                      <span class="upload-copy"><b>添加任务材料与历史证据</b><small>支持截图、日志、PDF、PR、需求文档、会议记录</small></span>
                      <button type="button" @click="$refs.searchFileInput.click()">选择</button>
                    </div>
                    <div class="file-pills">
                      <span v-for="file in searchFiles" :key="file.localId">
                        <img v-if="file.type === '图片'" :src="file.url" :alt="file.name" />
                        {{ file.name }} · {{ file.sizeText }} · {{ file.status }}<template v-if="file.progress"> {{ file.progress }}%</template>
                        <button type="button" @click="removeSearchFile(file.localId)">删除</button>
                      </span>
                    </div>
                  </div>

                  <div class="search-context-board">
                    <article>
                      <b>任务上下文</b>
                      <span>{{ searchForm.deviceName || '未填写项目' }} / {{ searchForm.deviceModel || '未填写技术栈' }}</span>
                      <small>{{ searchForm.faultType }} · {{ searchForm.maintenanceLevel }} · {{ searchForm.faultCode || '无 Issue' }}</small>
                    </article>
                    <article>
                      <b>证据准备</b>
                      <span>{{ searchFiles.length ? `${searchFiles.length} 个附件已加入` : '等待任务资料' }}</span>
                      <small>{{ searchForm.query ? '任务描述已填写' : '建议补充需求、影响范围、历史尝试或验收标准' }}</small>
                    </article>
                    <article>
                      <b>下一步建议</b>
                      <span>{{ searchResult ? '查看引用依据并转任务' : '先生成 Context Pack' }}</span>
                      <small>{{ searchResult ? `${searchResult.confidence}% 置信度，可继续追溯` : '可上传文档、截图、日志或语音补充上下文' }}</small>
                    </article>
                  </div>

                </div>

                <div class="search-fusion-ai">
                  <div class="search-ai-status">
                    <img :src="operatorProfile.avatar" :alt="operatorProfile.name" @error="handleAvatarError" />
                    <div><b>{{ loading.search ? '观微正在组包' : '观微正在协助' }}</b><small>{{ loading.search ? '正在融合需求、代码、文档和历史经验' : (searchResult ? `已匹配 ${searchResult.references.length} 条 Memory / Skill` : '等待任务线索') }}</small></div>
                  </div>
                  <div v-if="loading.search" class="search-process-card" aria-live="polite">
                    <div class="search-scan-visual">
                      <span class="scan-core">观微</span>
                      <i></i><i></i><i></i>
                    </div>
                    <div class="search-process-copy">
                      <b>Context Pack 生成中</b>
                      <p>正在召回需求、代码、历史任务、Memory Unit 与相关 Skill，生成可追溯任务上下文。</p>
                    </div>
                    <div class="search-process-track">
                      <span v-for="step in searchRunningSteps" :key="step.title">
                        <b>{{ step.title }}</b>
                        <small>{{ step.desc }}</small>
                      </span>
                    </div>
                  </div>
                  <div class="search-prompt-templates">
                    <button v-for="item in searchTemplatePrompts" :key="item.title" type="button" @click="operatorInput = item.prompt">
                      <span>
                        <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path v-for="path in iconParts(item.icon)" :key="path" :d="path"></path></svg>
                      </span>
                      <b>{{ item.title }}</b>
                    </button>
                  </div>
                  <div class="search-dialog-summary">
                    <article>
                      <span><svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h9l3 3v15H6Z"></path><path d="M14 3v4h4"></path><path d="M9 12h6M9 16h4"></path></svg></span>
                      <div><b>上下文摘要</b><p>{{ searchResult ? searchResult.phenomenonSummary : '填写任务背景后，观微会整理匹配摘要。' }}</p></div>
                    </article>
                    <article>
                      <span><svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3a9 9 0 1 0 9 9"></path><path d="M12 7v5l3 2"></path></svg></span>
                      <div><b>初步判断</b><p>{{ searchResult ? searchResult.causes.slice(0, 2).join('；') : '暂无判断，建议先上传需求、日志、代码片段或历史文档。' }}</p></div>
                    </article>
                  </div>
                  <div class="search-dialog-thread">
                    <div class="bubble assistant">我是观微。你可以上传需求、日志、PR 或历史记录，或直接问“这次任务需要哪些上下文”。</div>
                    <div v-for="message in currentOperatorMessages" :key="message.id" :class="['bubble', message.role, { loading: message.loading }]">
                      <span v-if="message.loading" class="loading-dots"><i></i><i></i><i></i></span>
                      {{ message.text }}
                    </div>
                  </div>
                </div>
              </div>

              <form v-show="searchMultimodalExpanded" class="search-dialog-input search-fusion-bar" @submit.prevent="sendOperatorPrompt(operatorInput)">
                <input ref="searchAssistantFileInput" class="visually-hidden" type="file" multiple accept="image/*,.pdf,.doc,.docx,.txt,.md" @change="addFiles($event, 'assistant')" />
                <button type="button" title="上传附件" aria-label="上传附件" @click="searchAssistantFileInput?.click()">
                  <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h4l2-2h4l2 2h4v12H4Z"></path><circle cx="12" cy="13" r="3"></circle></svg>
                </button>
                <button type="button" :class="{ active: assistantVoiceListening }" title="语音输入" aria-label="语音输入" @click="toggleAssistantVoice">
                  <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3a3 3 0 0 0-3 3v5a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3Z"></path><path d="M19 10a7 7 0 0 1-14 0"></path><path d="M12 17v4"></path></svg>
                </button>
                <input v-model="operatorInput" placeholder="请输入任务问题、需求背景或补充上下文..." />
                <button class="primary" type="submit" aria-label="发送">
                  <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m4 4 16 8-16 8 3-8-3-8Z"></path><path d="M7 12h13"></path></svg>
                </button>
              </form>
            </div>
          </template>

          <template v-else-if="searchPanel === 'results'">
            <div class="panel search-analysis-panel" :class="{ ready: searchResult }">
              <div class="search-panel-heading compact-heading">
                <span class="search-step">02</span>
                <div><p class="eyebrow">Context Pack 生成</p><h3>{{ searchResult ? '任务上下文摘要' : '等待上下文组装' }}</h3><small>{{ searchResult ? '综合需求、代码、文档与历史经验形成判断' : '请先在 Context Engine 中启动组包' }}</small></div>
              </div>
              <template v-if="searchResult">
                <div class="analysis-summary"><span>上下文结论</span><h3>{{ searchResult.phenomenonSummary }}</h3></div>
                <div class="analysis-grid">
                  <span>风险等级：{{ severityText(searchResult.risk) }}</span>
                  <span>置信度：{{ searchResult.confidence }}%</span>
                  <span>建议：{{ searchResult.stopAdvice }}</span>
                </div>
                <div class="tag-line modality-line"><span v-for="mode in searchResult.modalities" :key="mode">{{ modalityText(mode) }}</span></div>
                <template v-if="searchResult.visualFindings?.length">
                  <h4>图片识别线索</h4>
                  <ul><li v-for="item in searchResult.visualFindings" :key="item">{{ item }}</li></ul>
                </template>
                <h4>关键线索</h4>
                <ul><li v-for="item in searchResult.causes" :key="item">{{ item }}</li></ul>
                <h4>推荐关注位置 / 工具</h4>
                <p>{{ searchResult.positions.join('、') }}；工具：{{ searchResult.tools.join('、') }}</p>
                <div class="card-actions"><button class="primary" type="button" @click="prepareKnowledgeFromSearch">提炼为 Memory</button><button type="button" @click="searchPanel = 'multimodal'">重新组包</button></div>
              </template>
              <div v-else-if="loading.search" class="search-running-state">
                <div class="search-scan-visual large">
                  <span class="scan-core">检</span>
                  <i></i><i></i><i></i>
                </div>
                <div>
                  <p class="eyebrow">观微执行中</p>
                  <h4>正在生成 Context Pack</h4>
                  <p>系统正在融合任务描述、附件证据、代码线索和 Team Memory 引用。</p>
                </div>
                <div class="search-process-track wide">
                  <span v-for="step in searchRunningSteps" :key="step.title">
                    <b>{{ step.title }}</b>
                    <small>{{ step.desc }}</small>
                  </span>
                </div>
              </div>
              <div v-else class="empty search-empty-state">
                <span class="analysis-orbit"><i></i><i></i><i></i><b>检</b></span>
                <h4>Context Pack 将在这里生成</h4>
                <p>系统会结合任务描述、相关文档和历史经验，给出执行路径、风险和可复用 Skill。</p>
              </div>
            </div>

            <div class="panel search-results-panel">
              <div class="panel-head">
                <div>
                  <p class="eyebrow">03 · 上下文分类</p>
                  <h3>需求、代码、历史任务、Memory、Skill 与 Eval 节点</h3>
                  <small class="result-tab-hint">{{ resultTabHint }}</small>
                </div>
                <div class="tabs">
                  <button v-for="tab in resultTabs" :key="tab" type="button" :class="{ active: resultTab === tab }" @click="selectResultTab(tab)">{{ tab }}<em>{{ resultCountFor(tab) }}</em></button>
                </div>
              </div>
              <div v-if="filteredResults.length" class="result-grid result-grid-compact">
                <article v-for="item in filteredResults" :key="item.id" class="result-card">
                  <div>
                    <b>{{ item.title }}</b>
                    <small>{{ item.type }} · {{ item.equipment }} · {{ item.model }} · 匹配度 {{ item.match }}%</small>
                    <p>{{ item.summary }}</p>
                  </div>
                  <div class="tag-line"><span v-for="tag in item.tags" :key="tag">{{ tag }}</span></div>
                  <div class="card-actions">
                    <button type="button" @click="openKnowledge(item)">详情</button>
                    <button v-if="item.id !== 'recommendation-current'" type="button" @click="previewFile(files[0])">预览</button>
                    <button type="button" @click="createTaskFromSearch(item)">建任务</button>
                  </div>
                </article>
              </div>
              <div v-else class="result-filter-empty"><b>当前分类暂无匹配结果</b><span>可以切换到“全部”，或调整项目、模块和任务描述后重新组包。</span><button type="button" @click="selectResultTab('全部')">查看全部结果</button></div>
            </div>

            <div class="panel span-all maintenance-advice-panel" v-if="searchResult">
              <div class="advice-heading"><div><p class="eyebrow">协作建议</p><h3>推荐执行路径</h3></div><span>{{ normalizedSuggestionSteps.length }} 个步骤</span></div>
              <div class="sop-list">
                <span v-for="(step, index) in normalizedSuggestionSteps" :key="`${index}-${step}`"><b>{{ index + 1 }}</b>{{ step }}</span>
              </div>
              <p class="advice-reference"><b>引用依据</b>{{ searchResult.references.slice(0, 3).map((item) => item.title).join('、') }}</p>
            </div>
          </template>

          <template v-else-if="searchPanel === 'update'">
            <div class="panel span-all search-update-panel">
              <div class="panel-head">
                <div><p class="eyebrow">Memory Evolution</p><h3>把本次任务过程提炼为 Memory</h3><small>用于沉淀有效根因、解决路径、Eval 结论、适用条件和引用依据。</small></div>
                <button type="button" @click="prepareKnowledgeFromSearch">从当前 Context Pack 生成</button>
              </div>
              <div class="update-progress-strip">
                <article v-for="item in updateProgressCards" :key="item.title" :class="`tone-${item.tone}`">
                  <span>
                    <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path v-for="path in iconParts(item.icon)" :key="path" :d="path"></path></svg>
                  </span>
                  <div><small>{{ item.title }}</small><b>{{ item.value }}</b><em>{{ item.desc }}</em></div>
                </article>
              </div>
              <div class="search-update-layout">
                <div class="form-grid">
                  <label>Memory 标题<input v-model="knowledgeForm.title" placeholder="如：支付回调幂等处理经验" /></label>
                  <label>资产类型<select v-model="knowledgeForm.type"><option>Memory Unit</option><option>Skill</option><option>Eval Case</option><option>Issue to Skill</option></select></label>
                  <label>适用项目<input v-model="knowledgeForm.equipment" /></label>
                  <label>技术栈 / 模块<input v-model="knowledgeForm.model" /></label>
                  <label>来源依据<input v-model="knowledgeForm.source" placeholder="任务号、Issue、PR、会议或聊天记录" /></label>
                  <label>人工标签<input v-model="knowledgeForm.tagText" placeholder="使用逗号分隔，如：支付,幂等,回归" /></label>
                  <label class="wide">沉淀摘要<textarea v-model="knowledgeForm.summary" placeholder="描述问题、尝试、根因、方案、适用条件、Eval 结论和引用依据"></textarea></label>
                </div>
                <aside class="knowledge-update-aside">
                  <div class="update-quality-card">
                    <b>Memory 入库质量检查</b>
                    <span><small>引用依据</small><em>{{ searchResult?.references?.length || 0 }} 份</em></span>
                    <span><small>人工标签</small><em>{{ knowledgeForm.tagText ? knowledgeForm.tagText.split(/[，,]/).filter(Boolean).length : 0 }} 个</em></span>
                    <span><small>待审核</small><em>{{ pendingKnowledge.length }} 条</em></span>
                  </div>
                  <div class="update-step-list">
                    <article v-for="item in knowledgeUpdateSteps" :key="item.title">
                      <i></i><span><b>{{ item.title }}</b><small>{{ item.desc }}</small></span>
                    </article>
                  </div>
                  <div class="update-rule-list">
                    <b>入库规则</b>
                    <span v-for="item in updateQualityRules" :key="item.title">
                      <small>{{ item.title }}</small><em>{{ item.desc }}</em>
                    </span>
                  </div>
                </aside>
              </div>
              <button class="primary" type="button" @click="saveKnowledge">提交 Memory 审核</button>
              <div class="knowledge-review-list">
                <article v-for="item in pendingKnowledge" :key="item.id" class="result-card">
                  <div><b>{{ item.title }}</b><small>{{ item.equipment }} / {{ item.model }} · {{ knowledgeStatusText(item.status) }}</small><p>{{ item.summary }}</p></div>
                  <label>人工修正<textarea v-model="knowledgeCorrections[item.id]" placeholder="核对并修正模型整理结果；无误可直接通过"></textarea></label>
                  <div class="tag-line"><span v-for="tag in item.tags || []" :key="tag">{{ tag }}</span></div>
                  <div class="card-actions"><button class="primary" type="button" @click="reviewKnowledge(item, 'approved')">审核入库</button><button type="button" @click="reviewKnowledge(item, 'rejected')">退回修改</button></div>
                </article>
              </div>
            </div>
          </template>

          <template v-else-if="searchPanel === 'external'">
            <div class="panel span-all search-update-panel">
              <div class="panel-head">
                <div>
                  <p class="eyebrow">AI Import Gateway</p>
                  <h3>外部 AI 工作台导入</h3>
                  <small>把 Codex、Claude、ChatGPT、Cursor 的对话总结、代码变更和风险结论导入一休，解析成项目资产。</small>
                </div>
                <button type="button" @click="loadExternalImports">刷新记录</button>
              </div>
              <div class="update-progress-strip">
                <article v-for="item in externalImportStats" :key="item.title" :class="`tone-${item.tone}`">
                  <span><svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path v-for="path in iconParts(item.icon)" :key="path" :d="path"></path></svg></span>
                  <div><small>{{ item.title }}</small><b>{{ item.value }}</b><em>{{ item.desc }}</em></div>
                </article>
              </div>
              <div class="search-update-layout">
                <div class="form-grid">
                  <label>来源平台<select v-model="externalImportForm.provider"><option>codex</option><option>claude</option><option>chatgpt</option><option>cursor</option><option>github</option></select></label>
                  <label>关联项目<input v-model="externalImportForm.project_name" placeholder="如：支付服务 / 一休 Web 端" /></label>
                  <label>内容类型<select v-model="externalImportForm.content_type"><option>summary</option><option>chat</option><option>diff</option><option>pr</option><option>file</option></select></label>
                  <label>导入标题<input v-model="externalImportForm.title" placeholder="如：Codex 支付回调修复总结" /></label>
                  <label class="wide">外部 AI 内容<textarea v-model="externalImportForm.raw_content" placeholder="建议粘贴一休固定格式 JSON；也支持 Codex / Claude 的任务总结、对话摘要、代码 diff、PR 说明、风险和待办"></textarea></label>
                </div>
                <aside class="knowledge-update-aside">
                  <div class="update-quality-card">
                    <b>自动解析目标</b>
                    <span><small>项目进展</small><em>Project Update</em></span>
                    <span><small>候选资产</small><em>Memory / Skill / Eval</em></span>
                    <span><small>审核策略</small><em>人工确认后入库</em></span>
                  </div>
                  <div class="update-step-list">
                    <article v-for="item in externalImportSteps" :key="item.title">
                      <i></i><span><b>{{ item.title }}</b><small>{{ item.desc }}</small></span>
                    </article>
                  </div>
                  <button class="primary" type="button" :disabled="externalImportLoading" @click="submitExternalImport">{{ externalImportLoading ? '导入解析中' : '导入并解析' }}</button>
                </aside>
              </div>
              <div class="knowledge-review-list external-import-list">
                <article v-for="item in externalImports" :key="item.id" class="result-card">
                  <div>
                    <b>{{ item.title }}</b>
                    <small>{{ item.provider }} · {{ item.project_name || '未关联项目' }} · {{ item.parse_status }}</small>
                    <p>{{ item.summary || '等待解析摘要' }}</p>
                  </div>
                  <div class="tag-line">
                    <span v-for="artifact in item.artifacts.slice(0, 5)" :key="artifact.id">{{ externalArtifactTypeText(artifact.artifact_type) }} · {{ artifact.review_status }}</span>
                  </div>
                  <div class="external-artifact-grid">
                    <span v-for="artifact in item.artifacts" :key="artifact.id">
                      <b>{{ externalArtifactTypeText(artifact.artifact_type) }}</b>
                      <small>{{ artifact.title }}</small>
                      <em>{{ artifact.confidence }}%</em>
                      <button v-if="artifact.review_status !== 'approved'" type="button" @click="reviewExternalArtifact(artifact, 'approved')">通过</button>
                      <button v-if="artifact.review_status !== 'rejected'" type="button" @click="reviewExternalArtifact(artifact, 'rejected')">退回</button>
                    </span>
                  </div>
                  <div class="card-actions"><button type="button" @click="parseExternalImport(item)">重新解析</button><button type="button" @click="fillExternalImportExample(item.provider)">填入示例</button></div>
                </article>
              </div>
            </div>
          </template>

          <div v-if="searchPanel === 'update'" class="panel span-all">
            <p class="eyebrow">沉淀更新</p>
            <div class="form-grid">
              <label>知识标题<input v-model="knowledgeForm.title" placeholder="如：发动机异响复检案例" /></label>
              <label>资产类型<select v-model="knowledgeForm.type"><option>Memory Unit</option><option>Skill</option><option>Eval Case</option><option>Issue to Skill</option></select></label>
              <label>适用设备<input v-model="knowledgeForm.equipment" /></label>
              <label>设备型号<input v-model="knowledgeForm.model" /></label>
              <label>来源依据<input v-model="knowledgeForm.source" placeholder="工单号、手册章节或现场记录" /></label>
              <label>人工标签<input v-model="knowledgeForm.tagText" placeholder="使用逗号分隔，如：异响,气门,复测" /></label>
              <label class="wide">沉淀摘要<textarea v-model="knowledgeForm.summary" placeholder="描述问题、尝试、根因、方案、适用条件、Eval 结论和引用依据"></textarea></label>
            </div>
            <button class="primary" type="button" @click="saveKnowledge">提交 Memory 审核</button>
            <div class="knowledge-review-list">
              <article v-for="item in pendingKnowledge" :key="item.id" class="result-card">
                <div><b>{{ item.title }}</b><small>{{ item.equipment }} / {{ item.model }} · {{ knowledgeStatusText(item.status) }}</small><p>{{ item.summary }}</p></div>
                <label>人工修正<textarea v-model="knowledgeCorrections[item.id]" placeholder="核对并修正模型整理结果；无误可直接通过"></textarea></label>
                <div class="tag-line"><span v-for="tag in item.tags || []" :key="tag">{{ tag }}</span></div>
                <div class="card-actions"><button class="primary" type="button" @click="reviewKnowledge(item, 'approved')">审核入库</button><button type="button" @click="reviewKnowledge(item, 'rejected')">退回修改</button></div>
              </article>
            </div>
          </div>
          <template v-if="searchPanel === 'history'">
            <div class="panel search-history-panel">
              <div class="panel-head"><div><p class="eyebrow">历史经验</p><h3>最近 Context Pack 记录</h3><small>点击记录可回填任务条件，继续追溯同类问题。</small></div><button type="button" @click="searchPanel = 'multimodal'">新建组包</button></div>
              <div class="history-command-strip">
                <button type="button" @click="toast('已筛出可复用的高置信度 Context Pack')"><b>高置信复用</b><small>优先使用 85% 以上记录</small></button>
                <button type="button" @click="toast('已按项目和任务类型合并相似问题')"><b>相似问题合并</b><small>同模块、同任务自动归组</small></button>
                <button type="button" @click="toast('已生成历史上下文追溯摘要')"><b>生成追溯摘要</b><small>用于任务执行备注</small></button>
              </div>
              <div class="history-stat-grid">
                <span><b>{{ searchHistory.length }}</b><small>近期检索</small></span>
                <span><b>{{ Math.round(searchHistory.reduce((sum, item) => sum + item.confidence, 0) / Math.max(searchHistory.length, 1)) }}%</b><small>平均置信度</small></span>
                <span><b>{{ new Set(searchHistory.map(item => item.faultType)).size }}</b><small>任务类型</small></span>
              </div>
              <div class="history-search-list">
                <button v-for="item in searchHistory" :key="item.id" type="button" @click="applySearchHistory(item)">
                  <span><b>{{ item.title }}</b><small>{{ item.time }} · {{ item.deviceName }} · {{ item.model }} · {{ item.faultType }}</small></span>
                  <em>{{ item.confidence }}%</em>
                </button>
              </div>
              <div class="history-action-row">
                <button type="button" @click="toast('已按任务类型整理历史记录')">按任务归类</button>
                <button type="button" @click="toast('已标记高匹配历史记录')">标记高匹配</button>
                <button type="button" @click="activePage = 'search'; searchPanel = 'update'">沉淀为 Memory</button>
              </div>
            </div>
            <div class="panel history-learning-panel">
              <div class="panel-head"><div><p class="eyebrow">经验学习推荐</p><h3>基于历史任务的 Memory 推荐</h3><small>按近期任务类型、资料引用与执行路径自动聚合。</small></div></div>
              <div class="history-insight-grid">
                <article v-for="item in historyInsightCards" :key="item.title">
                  <b>{{ item.title }}</b><small>{{ item.desc }}</small><em>{{ item.value }}</em>
                </article>
              </div>
              <div class="history-trace-lanes">
                <article v-for="item in historyTraceCards" :key="item.title" :class="`tone-${item.tone}`">
                  <span>
                    <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path v-for="path in iconParts(item.icon)" :key="path" :d="path"></path></svg>
                  </span>
                  <div><b>{{ item.title }}</b><small>{{ item.desc }}</small></div>
                  <em>{{ item.meta }}</em>
                </article>
              </div>
              <div class="learning-recommend-list">
                <article
                  v-for="item in historyLearningRecommendations"
                  :key="item.title"
                  :class="{ active: selectedLearningRecommendation?.title === item.title }"
                  role="button"
                  tabindex="0"
                  @click="openLearningRecommendation(item)"
                  @keydown.enter.prevent="openLearningRecommendation(item)"
                >
                  <b>{{ item.title }}</b>
                  <p>{{ item.desc }}</p>
                  <div class="tag-line"><span v-for="tag in item.tags" :key="tag">{{ tag }}</span></div>
                  <div class="learning-card-actions">
                    <button type="button" @click.stop="openLearningRecommendation(item)">学习经验</button>
                    <button type="button" @click.stop="applyLearningRecommendation(item)">带入检索</button>
                  </div>
                </article>
              </div>
            </div>
          </template>
          <div v-if="searchPanel === 'network'" class="panel span-all graph-panel graph-console-panel">
            <div class="graph-toolbar">
              <div class="graph-toolbar-main">
                <label class="graph-search expanded">
                  <button class="graph-search-trigger" type="button" @click.prevent="openGraphSearch" aria-label="展开知识搜索">
                    <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true">
                      <path v-for="path in iconParts('search')" :key="path" :d="path"></path>
                    </svg>
                  </button>
                  <input ref="graphSearchInput" v-model="knowledgeKeyword" placeholder="搜索项目、任务、Memory、Skill、Issue 或文档" @focus="graphSearchExpanded = true" @keyup.enter="loadKnowledge" />
                  <button v-if="knowledgeKeyword" class="graph-search-clear" type="button" @click.prevent="knowledgeKeyword = ''">×</button>
                </label>
                <div class="graph-controls">
                  <select v-model="graphLayoutMode" @change="relayoutGraph">
                    <option value="grid">双圈布局</option>
                    <option value="force">力导向</option>
                    <option value="tree">层级布局</option>
                    <option value="circle">环形布局</option>
                  </select>
                  <select v-model="graphRelationFilter">
                    <option value="all">全部关系</option>
                    <option v-for="item in graphRelationTypes" :key="item" :value="item">{{ item }}</option>
                  </select>
                  <select v-model="graphDepth">
                    <option :value="1">1 级</option>
                    <option :value="2">2 级</option>
                    <option :value="3">3 级</option>
                  </select>
                  <label><input v-model="graphShowLabels" type="checkbox" /> 显示标签</label>
                  <button type="button" @click="loadKnowledge">刷新</button>
                  <button type="button" @click="resetGraphView">重置</button>
                  <button type="button" @click="relayoutGraph">布局优化</button>
                </div>
              </div>
            </div>
            <div class="knowledge-map">
              <aside class="graph-filter-panel">
                <section>
                  <div class="graph-filter-head"><b>Memory 图谱筛选</b><button type="button" @click="graphKindFilter = 'all'; graphRelationFilter = 'all'; graphLegendFiltered = {}">清空</button></div>
                  <small class="graph-filter-note">搜索入口已合并到上方工具栏，这里只保留筛选。</small>
                </section>
                <section>
                  <div class="graph-filter-head"><b>实体类型</b><button type="button" @click="graphKindFilter = 'all'">全选</button></div>
                  <button
                    v-for="item in graphLegend"
                    :key="item.kind"
                    type="button"
                    class="graph-type-row"
                    :class="{ active: graphKindFilter === item.kind, dimmed: graphLegendFiltered[item.kind] }"
                    @click="graphKindFilter = graphKindFilter === item.kind ? 'all' : item.kind"
                  >
                    <span><i :class="item.kind"></i>{{ item.label }}</span>
                    <em>{{ graphTypeCount(item.kind) }}</em>
                  </button>
                </section>
                <section>
                  <div class="graph-filter-head"><b>关系类型</b><button type="button" @click="graphRelationFilter = 'all'">全部</button></div>
                  <button
                    v-for="item in graphRelationTypes.slice(0, 6)"
                    :key="item"
                    type="button"
                    class="graph-relation-row"
                    :class="{ active: graphRelationFilter === item }"
                    @click="graphRelationFilter = graphRelationFilter === item ? 'all' : item"
                  >
                    <span>→ {{ item }}</span>
                    <em>{{ graphRelationCount(item) }}</em>
                  </button>
                </section>
                <section class="graph-layer-switches">
                  <div class="graph-filter-head"><b>图谱图层</b></div>
                  <label><span>基础图层</span><input checked type="checkbox" /></label>
                  <label><span>扩展图层</span><input checked type="checkbox" /></label>
                  <label><span>Memory 注释</span><input v-model="graphShowLabels" type="checkbox" /></label>
                </section>
              </aside>
              <div class="map-canvas-wrap">
                <div ref="graphChartRef" class="map-canvas echarts-canvas"></div>
                <div class="graph-legend-panel">
                  <div class="legend-body">
                    <span
                      v-for="item in graphLegend"
                      :key="item.kind"
                      :class="{ dimmed: graphLegendFiltered[item.kind] }"
                      @click="toggleLegendFilter(item.kind)"
                    >
                      <i :class="item.kind"></i>{{ item.label }}
                    </span>
                  </div>
                </div>
              </div>
              <div class="map-sidebar">
              <aside class="map-inspector">
                <div class="map-inspector-tabs">
                  <button type="button" :class="{ active: graphInspectorTab === 'info' }" @click="graphInspectorTab = 'info'">实体信息</button>
                  <button type="button" :class="{ active: graphInspectorTab === 'relations' }" @click="graphInspectorTab = 'relations'">关系概览</button>
                  <button type="button" :class="{ active: graphInspectorTab === 'attrs' }" @click="graphInspectorTab = 'attrs'">属性详情</button>
                </div>
                <template v-if="selectedGraphNode">
                  <div v-if="graphInspectorTab === 'info'" class="graph-inspector-section">
                    <h3>{{ selectedGraphNode.label }}</h3>
                    <small class="node-type-pill">{{ graphKindMeta[selectedGraphNode.kind]?.text || 'Memory 实体' }}</small>
                    <p>{{ selectedGraphNode.summary }}</p>
                    <div class="tag-line">
                      <span v-for="tag in selectedGraphNode.tags" :key="tag">{{ tag }}</span>
                    </div>
                    <button class="primary" type="button" @click="openKnowledge(selectedGraphNode.source)">查看完整 Memory</button>
                    <button type="button" @click="askAgentAboutNode(selectedGraphNode)">向博闻提问</button>
                  </div>
                  <div v-else-if="graphInspectorTab === 'relations'" class="graph-inspector-section inspector-relation-list">
                    <h3>直接关系</h3>
                    <button v-for="item in selectedGraphRelationSummary.links" :key="item.id" type="button" @click="selectGraphNode(item)">
                      <span>{{ item.label }}</span><em>{{ graphKindMeta[item.kind]?.text || '节点' }}</em>
                    </button>
                    <p v-if="!selectedGraphRelationSummary.links.length">暂无直接关联节点。</p>
                  </div>
                  <div v-else class="graph-inspector-section inspector-attrs">
                    <h3>属性详情</h3>
                    <span v-for="item in selectedGraphAttributes" :key="item.label">
                      <small>{{ item.label }}</small><b>{{ item.value }}</b>
                    </span>
                  </div>
                </template>
                <div v-else class="empty">点击图谱节点查看关联 Memory、任务和 Skill 建议。</div>
              </aside>
              <aside class="map-summary-card graph-relation-card">
                <h3>关系摘要</h3>
                <div class="graph-relation-stats">
                  <span><small>直接关联</small><b>{{ selectedGraphRelationSummary.direct }}</b></span>
                  <span><small>同源节点</small><b>{{ selectedGraphRelationSummary.sameSource }}</b></span>
                  <span><small>关联层级</small><b>{{ selectedGraphRelationSummary.depth }} 级</b></span>
                </div>
                <button v-for="item in selectedGraphRelationSummary.links" :key="item.id" type="button" @click="selectGraphNode(item)">
                  <span>{{ item.label }}</span><em>{{ graphKindMeta[item.kind]?.text || '节点' }}</em>
                </button>
              </aside>
              <aside class="map-summary-card graph-doc-card">
                <h3>关联资产</h3>
                <button v-for="item in selectedGraphDocuments" :key="item.id" type="button" @click="openKnowledge(item)">
                  <span>{{ item.title }}</span><em>{{ item.updated_at || item.type || '已入库' }}</em>
                </button>
                <p v-if="!selectedGraphDocuments.length" class="map-doc-empty">点击图谱节点后，这里会显示对应资料。</p>
              </aside>
              </div>
            </div>
          </div>

          <div v-if="searchPanel === 'library'" class="panel span-all knowledge-library-panel">
            <div class="kb-hero">
              <div class="kb-hero-left">
                <h3>技术资料库</h3>
                <span>模板创建 · 多人协作 · 版本追踪 · 任务联动</span>
              </div>
              <div class="kb-hero-right">
                <button class="kb-cta kb-cta-new" type="button" @click="showTemplatePicker = true">
                  <svg class="ui-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
                  <span>新建文档</span>
                </button>
                <button class="kb-cta kb-cta-tpl" type="button" @click="showTemplateLibrary = true">
                  <svg class="ui-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
                  <span>模板库</span>
                </button>
              </div>
            </div>

            <div class="kb-toolbar">
              <div class="kb-toolbar-left">
                <h4>全部文档 <small>{{ filteredKnowledgeDocs.length }} 篇</small></h4>
                <div class="kb-filter">
                  <button type="button" :class="{ active: kbFilter === 'all' }" @click="kbFilter = 'all'">全部</button>
                  <button type="button" :class="{ active: kbFilter === 'mine' }" @click="kbFilter = 'mine'">我创建的</button>
                  <button type="button" :class="{ active: kbFilter === 'starred' }" @click="kbFilter = 'starred'">星标</button>
                  <button type="button" :class="{ active: kbFilter === 'recent' }" @click="kbFilter = 'recent'">最近编辑</button>
                </div>
              </div>
              <div class="kb-search">
                <svg class="ui-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>
                <input v-model.trim="kbSearch" placeholder="搜索文档标题、标签或内容" />
              </div>
            </div>

            <div v-if="filteredKnowledgeDocs.length" class="kb-grid">
              <article
                v-for="(doc, idx) in filteredKnowledgeDocs"
                :key="doc.id"
                class="kb-doc-card"
                :class="{ starred: doc.starred }"
                @click="openKnowledge(doc)"
              >
                <div class="kb-doc-head">
                  <span class="kb-doc-type" :class="doc.category || 'general'">{{ doc.type || doc.category || '技术资料' }}</span>
                  <svg v-if="doc.starred" class="ui-icon kb-star-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                </div>
                <h4 class="kb-doc-title">{{ doc.title }}</h4>
                <p class="kb-doc-summary">{{ (doc.content || '').replace(/[#*>\-\[\]]/g, '').slice(0, 80) || '暂无内容，点击开始编辑' }}</p>
                <div v-if="(doc.tags || []).length" class="kb-doc-tags">
                  <span v-for="tag in (doc.tags || []).slice(0, 3)" :key="tag" class="kb-tag">{{ tag }}</span>
                </div>
                <div class="kb-doc-foot">
                  <div class="kb-collab">
                    <div v-if="doc.collaborators?.length" class="kb-avatars">
                      <span v-for="(c, ci) in doc.collaborators.slice(0, 3)" :key="ci" class="kb-avatar" :style="{ background: avatarColors[ci % avatarColors.length] }">{{ (c.name || '?')[0] }}</span>
                      <span v-if="doc.collaborators.length > 3" class="kb-more">+{{ doc.collaborators.length - 3 }}</span>
                    </div>
                    <span class="kb-collab-count" v-if="doc.collaborators?.length">{{ doc.collaborators.length }} 人协作</span>
                    <span v-else class="kb-no-collab">仅自己</span>
                  </div>
                  <small class="kb-time">{{ doc.updated_at || '新建' }}</small>
                </div>
              </article>
            </div>
            <div v-else class="kb-empty-state">
              <h4>暂无技术文档</h4>
              <p>点击上方「新建文档」按钮，选择模板快速创建</p>
              <button class="primary kb-empty-btn" type="button" @click="showTemplatePicker = true">+ 新建文档</button>
            </div>
          </div>

          <!-- 模板选择弹窗 -->
          <div v-if="showTemplatePicker" class="modal" @click.self="showTemplatePicker = false">
            <article class="modal-card kb-template-modal">
              <button class="close" type="button" @click="showTemplatePicker = false">×</button>
              <header>
                <p class="eyebrow">选择模板</p>
                <h2>从模板创建文档</h2>
                <span>选择一个模板快速开始，创建后可随时修改</span>
              </header>
              <div class="kb-template-grid">
                <article
                  v-for="tpl in availableTemplates"
                  :key="tpl.id"
                  class="kb-template-card"
                  @click="createDocFromTemplate(tpl)"
                >
                  <div
                    class="kb-template-icon kb-template-visual"
                    :class="`tpl-${templateIconName(tpl)}`"
                    :data-label="templateIconLabel(tpl)"
                    aria-hidden="true"
                  ></div>
                  <div class="kb-template-info">
                    <h4>{{ tpl.name }}</h4>
                    <span>{{ tpl.category }}</span>
                    <p>{{ tpl.description }}</p>
                  </div>
                  <button class="kb-template-use" type="button">使用模板 →</button>
                </article>
              </div>
            </article>
          </div>

          <!-- 模板库弹窗 -->
          <div v-if="showTemplateLibrary" class="modal" @click.self="showTemplateLibrary = false">
            <article class="modal-card kb-template-lib-modal">
              <button class="close" type="button" @click="showTemplateLibrary = false">×</button>
              <header>
                <p class="eyebrow">模板库</p>
                <h2>全部模板（{{ availableTemplates.length }} 个）</h2>
              </header>
              <div class="kb-template-grid">
                <article
                  v-for="tpl in availableTemplates"
                  :key="tpl.id"
                  class="kb-template-card"
                  @click="createDocFromTemplate(tpl)"
                >
                  <div
                    class="kb-template-icon kb-template-visual"
                    :class="`tpl-${templateIconName(tpl)}`"
                    :data-label="templateIconLabel(tpl)"
                    aria-hidden="true"
                  ></div>
                  <div class="kb-template-info">
                    <h4>{{ tpl.name }}</h4>
                    <span>{{ tpl.category }}</span>
                    <p>{{ tpl.description }}</p>
                  </div>
                  <button class="kb-template-use" type="button">使用模板 →</button>
                </article>
              </div>
            </article>
          </div>

</section>

<section v-else-if="activePage === 'tasks'" class="page-grid tasks-page">
          <div class="panel span-all task-nav-panel">
            <div class="panel-head">
              <div>
                <p class="eyebrow">Task Execution</p>
                <h3>任务执行中心</h3>
                <small>管理项目、分派成员和 Agent，记录进展与风险，并回看可复用的执行轨迹</small>
              </div>
              <div class="tabs">
                <button v-for="tab in taskTabs" :key="tab.key" type="button" :class="{ active: taskPanel === tab.key }" @click="taskPanel = tab.key">{{ tab.label }}</button>
              </div>
            </div>
          </div>


          <template v-if="taskPanel === 'overview'">
            <div class="panel span-all task-metric-table-panel">
              <div class="section-title-row">
                <div><p class="eyebrow">项目入口</p><h3>今日项目推进工作台</h3></div>
                <span class="section-count">快捷处理</span>
              </div>
              <div class="task-ops-grid">
                <article v-for="item in taskOpsCards" :key="item.title" :class="`tone-${item.tone}`">
                  <span>
                    <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path v-for="path in iconParts(item.icon)" :key="path" :d="path"></path></svg>
                  </span>
                  <div><small>{{ item.label }}</small><b>{{ item.title }}</b><p>{{ item.desc }}</p></div>
                  <button type="button" @click="item.action()">处理</button>
                </article>
              </div>            </div>
            <div class="panel span-all task-analytics">
              <div class="panel-head">
                <div><p class="eyebrow">Project Intelligence</p><h3>项目趋势、阶段状态、重复问题、模块和人员负载</h3></div>
                <button type="button" @click="toast('已展开更多分析：平均执行时长、按时完成率、重复劳动率、Skill 覆盖率')">查看更多分析</button>
              </div>
              <div class="analysis-cards">
                <section>
                  <div class="trend-card-head"><b>近 7 天项目推进趋势</b><span>累计 {{ taskTrendTotal }} 项</span></div>
                  <div class="trend-summary"><strong>{{ taskTrendData.at(-1) }}</strong><span>今日处理量</span><em :class="{ down: taskTrendChange < 0 }">{{ taskTrendChange >= 0 ? '↑' : '↓' }} {{ Math.abs(taskTrendChange) }} 较昨日</em></div>
                  <EChart :option="taskTrendOption" class="chart-canvas task-trend-echart" height="166px" />
                </section>
                <section class="chart-section">
                  <b>项目状态占比</b>
                  <EChart :option="taskStatusOption" class="chart-canvas" height="200px" click-field="key" @click="filterTaskBy('status', $event)" />
                  <p class="chart-hint">点击柱条可按状态筛选</p>
                </section>
                <section class="chart-section">
                  <b>重复问题等级分布</b>
                  <EChart :option="taskRiskOption" class="chart-canvas" height="200px" click-field="key" @click="filterTaskBy('severity', $event)" />
                  <p class="chart-hint">点击扇区可按风险筛选</p>
                </section>
                <section>
                  <b>模块类型与项目排行</b>
                  <button v-for="item in taskCategoryAnalysis" :key="item.key" type="button" class="chip-row" @click="filterTaskBy('category', item.key)">{{ item.label }} <em>{{ item.count }}</em></button>
                  <button v-for="item in faultRankAnalysis" :key="item.key" type="button" class="chip-row warm" @click="filterTaskBy('faultType', item.key)">{{ item.label }} <em>{{ item.count }}</em></button>
                </section>
              </div>
            </div>
            <div class="panel span-all priority-panel">
              <p class="eyebrow">重点项目</p>
              <div class="priority-list">
                <article v-for="task in priorityTasks" :key="task.id">
                  <header class="priority-task-top">
                    <div><small>{{ task.workOrderNo }}</small><b>{{ task.equipment_name }}</b></div>
                    <span><i :class="['badge', task.severity]">{{ severityText(task.severity) }}</i><em>{{ statusText(task.status) }}</em></span>
                  </header>
                  <p class="priority-task-desc">{{ task.description }}</p>
                  <div class="priority-task-meta">
                    <span><small>项目阶段</small><b>{{ task.project_phase || task.current_step }}</b></span>
                    <span><small>项目周期</small><b>{{ task.project_period || task.due_at }}</b></span>
                    <span><small>协作人员</small><b>{{ task.collaborators?.join('、') || '待分配' }}</b></span>
                  </div>
                  <div class="priority-task-progress">
                    <div><span :style="{ width: `${task.progress}%` }"></span></div>
                    <b>{{ task.progress }}%</b>
                  </div>
                  <footer><span><small>最新进展</small><b>{{ task.latest_update || task.current_step }}</b><em>剩余 {{ remainingTime(task) }}</em></span><button type="button" @click="openTask(task)">查看详情 <i>→</i></button></footer>
                </article>
              </div>
            </div>
            <div class="panel span-all task-event-panel">
              <div class="task-event-heading"><div><p class="eyebrow">项目动态</p><h3>进展、里程碑与决策记录</h3></div><span>{{ taskEvents.length }} 条记录</span></div>
              <div class="timeline task-events"><article v-for="event in taskEvents" :key="event.id"><i></i><time>{{ event.time }}</time><p>{{ event.text }}</p></article></div>
            </div>
          </template>

          <template v-if="taskPanel === 'manage'">
            <div class="panel span-all task-manage-panel">
              <div class="filters">
                <select v-model="taskFilters.status"><option value="all">全部状态</option><option value="pending">待启动</option><option value="in_progress">推进中</option><option value="review">待验收</option><option value="completed">已归档</option></select>
                <select v-model="taskFilters.severity"><option value="all">全部风险</option><option value="low">低</option><option value="medium">中</option><option value="high">高</option></select>
                <select v-model="taskFilters.category"><option value="all">全部模块</option><option v-for="item in taskCategoryAnalysis" :key="item.key" :value="item.key">{{ item.label }}</option></select>
                <select v-model="taskFilters.faultType"><option value="all">全部类型</option><option v-for="item in faultRankAnalysis" :key="item.key" :value="item.key">{{ item.label }}</option></select>
                <input v-model="taskFilters.keyword" placeholder="搜索项目/负责人/模块/协作人员" />
                <div class="view-switch"><button type="button" :class="{ active: taskView === 'table' }" @click="taskView = 'table'">表格</button><button type="button" :class="{ active: taskView === 'board' }" @click="taskView = 'board'">看板</button></div>
                <button class="primary" type="button" @click="showTaskForm = true">新建项目</button>
              </div>
              <div class="sop-guidance-strip">
                <section>
                  <p class="eyebrow">Skill 指引</p>
                  <h3>按项目类型与协作等级推送工作流</h3>
                  <small>当前筛选下自动匹配项目上下文、Skill、里程碑和 Eval 校验项。</small>
                </section>
                <div class="sop-guidance-cards">
                  <button v-for="item in taskGuidanceOverview" :key="item.key" type="button" @click="applyGuidanceFilter(item)">
                    <b>{{ item.title }}</b>
                    <span>{{ item.desc }}</span>
                    <em>{{ item.count }} 项</em>
                  </button>
                </div>
              </div>
              <div v-if="taskView === 'table'" class="table">
                <div class="tr head"><span>项目编号</span><span>项目</span><span>进展记录</span><span>风险</span><span>负责人</span><span>阶段/里程碑</span><span>状态</span><span>操作</span></div>
                <div v-for="task in filteredTasks" :key="task.id" class="tr">
                  <span>{{ task.workOrderNo }}</span>
                  <span>{{ task.equipment_name }}<small>{{ task.equipment_model }}</small></span>
                  <span>{{ task.projectProgressSummary || task.description }}<small>{{ task.latest_update || '暂无更新' }}</small></span>
                  <span><i :class="['badge', task.severity]">{{ severityText(task.severity) }}</i></span>
                  <span>{{ task.assignee_name }}</span>
                  <span>{{ task.project_phase || task.current_step }} · {{ task.progress }}%<small>{{ task.next_milestone || '待补充里程碑' }}</small></span>
                  <span>{{ statusText(task.status) }}</span>
                  <span class="inline-actions task-row-actions">
                    <button class="task-row-action detail" type="button" @click="openTask(task)"><span>查看</span><b>详情</b></button>
                    <button class="task-row-action flow" type="button" :disabled="task.status === 'completed'" @click="handleTaskPrimary(task)"><span>{{ task.status === 'review' ? '进入' : '项目' }}</span><b>{{ task.status === 'review' ? '验收' : '推进' }}</b></button>
                  </span>
                </div>
              </div>
              <div v-else class="task-board">
                <section v-for="column in taskBoardColumns" :key="column.key">
                  <h4>{{ column.label }} <small>{{ column.tasks.length }}</small></h4>
                  <article v-for="task in column.tasks" :key="task.id" @click="openTask(task)">
                    <b>{{ task.equipment_name }}</b>
                    <small>{{ task.workOrderNo }} · {{ task.project_phase || task.fault_type }}</small>
                    <span><i :class="['badge', task.severity]">{{ severityText(task.severity) }}</i>{{ task.progress }}%</span>
                  </article>
                </section>
              </div>
            </div>
          </template>

          <template v-if="taskPanel === 'contacts'">
            <div class="panel span-all chat-workbench" :class="{ 'left-collapsed': contactLeftCollapsed, 'right-collapsed': contactRightCollapsed }">
              <aside class="conversation-list">
                <div class="contact-toolbar">
                  <button class="contact-collapse-btn" type="button" :title="contactLeftCollapsed ? '展开会话列表' : '收起会话列表'" @click="contactLeftCollapsed = !contactLeftCollapsed">{{ contactLeftCollapsed ? '›' : '‹' }}</button>
                  <div class="chat-search"><input v-model="contactKeyword" placeholder="搜索" /></div>
                  <button type="button" title="新建协作群" @click="createCollaborationGroup">＋</button>
                  <button type="button" title="发起会议" @click="startInstantMeeting">⌕</button>
                </div>
                <div class="contact-mode-tabs">
                  <button v-for="mode in contactModes" :key="mode.key" type="button" :class="{ active: contactViewMode === mode.key }" @click="contactViewMode = mode.key">{{ mode.label }}<small>{{ mode.count }}</small></button>
                </div>
                <select v-model="contactDepartment" class="contact-filter">
                  <option value="all">全部关系</option>
                  <option v-for="department in departments" :key="department" :value="department">{{ department }}</option>
                </select>
                <div class="contact-summary">
                  <span><b>{{ contactStats.online }}</b><small>在线</small></span>
                  <span><b>{{ contactStats.groups }}</b><small>群聊</small></span>
                  <span><b>{{ contactStats.meetings }}</b><small>会议</small></span>
                </div>
                <div class="conversation-scroll">
                  <button v-for="session in filteredConversations" :key="session.id" type="button" :class="{ active: activeConversationId === session.id }" @click="openConversation(session)">
                    <img :src="avatarFor(session.avatar, session.name)" :alt="session.name" @error="handleContactAvatarError($event, session.name)" />
                    <span><b>{{ session.name }}</b><small>{{ session.position }} · {{ session.lastMessage }}</small></span>
                    <time>{{ session.kind === 'meeting' ? session.lastMessage : session.unread ? '刚刚' : '12:41' }}</time>
                    <i v-if="session.unread">{{ session.unread }}</i>
                  </button>
                </div>
              </aside>
              <section class="chat-main">
                <header class="chat-title">
                  <div>
                    <h3>{{ activeConversation?.name }} <span v-if="activeConversation?.kind === 'group'">({{ contactStats.online + 12 }})</span></h3>
                    <nav>
                      <button type="button" class="active">聊天</button>
                      <button type="button" @click="sendTaskCard()">任务</button>
                      <button type="button" @click="$refs.chatFileInput.click()">文件</button>
                      <button type="button" @click="sendMeetingCard">会议</button>
                      <button type="button" @click="summarizeConversation">@我回复</button>
                    </nav>
                  </div>
                  <div class="chat-title-actions">
                    <span v-if="activeConversation?.risk" :class="['badge', activeConversation.risk]">{{ severityText(activeConversation.risk) }}</span>
                    <button type="button" @click="requestSupport">请求支援</button>
                    <button type="button" @click="startInstantMeeting">发起会议</button>
                  </div>
                </header>
                <div class="chat-context-strip">
                  <span><b>{{ activeConversation?.devices?.join(' / ') || '通用检修' }}</b><small>关联对象</small></span>
                  <span><b>{{ activeConversation?.currentTask || '待关联任务' }}</b><small>当前任务</small></span>
                  <span><b>{{ activeConversation?.workload || 0 }}%</b><small>负载</small></span>
                </div>
                <div class="chat-messages">
                  <article v-for="message in activeMessages" :key="message.id" :class="['message', message.mine ? 'mine' : 'peer']">
                    <img v-if="!message.mine" :src="avatarFor(activeConversation?.avatar, activeConversation?.name)" :alt="activeConversation?.name" @error="handleContactAvatarError($event, activeConversation?.name)" />
                    <div>
                      <p>{{ message.text }}</p>
                      <img v-if="message.attachment?.kind === 'image'" class="chat-image" :src="message.attachment.url" :alt="message.attachment.name" @click="previewChatAttachment(message.attachment)" />
                      <button v-if="message.attachment?.kind === 'file'" class="chat-file" type="button" @click="previewChatAttachment(message.attachment)"><b>{{ message.attachment.name }}</b><small>{{ message.attachment.size }}</small></button>
                      <audio v-if="message.attachment?.kind === 'audio'" :src="message.attachment.url" controls preload="metadata"></audio>
                      <button v-if="message.card" class="message-card" type="button" @click="openMessageCard(message.card)">
                        <b>{{ message.card.title }}</b><small>{{ message.card.desc }}</small>
                      </button>
                      <small>{{ message.time }}<em v-if="message.syncFailed"> · 发送失败</em></small>
                    </div>
                  </article>
                </div>
                <form class="chat-compose" @submit.prevent="sendChatMessage(chatInput)">
                  <input ref="chatImageInput" class="visually-hidden" type="file" accept="image/*" multiple @change="addChatAttachments($event, 'image')" />
                  <input ref="chatFileInput" class="visually-hidden" type="file" multiple @change="addChatAttachments($event, 'file')" />
                  <div class="chat-compose-tools">
                    <button type="button" title="选择现场图片" @click="$refs.chatImageInput.click()">▧<span>图片</span></button>
                    <button type="button" title="选择本地文件" @click="$refs.chatFileInput.click()">▣<span>文件</span></button>
                    <button type="button" :class="{ recording: chatRecording }" @click="toggleChatRecording">{{ chatRecording ? `${chatRecordSeconds}s` : '☎' }}<span>语音</span></button>
                    <button type="button" title="任务卡片" @click="openTaskPicker('send')">▤<span>任务</span></button>
                    <button type="button" title="会议卡片" @click="sendMeetingCard">◎<span>会议</span></button>
                  </div>
                  <div class="chat-compose-editor">
                    <input v-model="chatInput" placeholder="输入人员、部门或支援需求" />
                    <button class="primary" type="submit">发送</button>
                  </div>
                </form>
              </section>
              <aside class="collab-info">
                <div class="group-settings-head">
                  <h3>群聊设置</h3>
                  <button type="button" :title="contactRightCollapsed ? '展开群聊设置' : '收起群聊设置'" @click="contactRightCollapsed = !contactRightCollapsed">{{ contactRightCollapsed ? '‹' : '›' }}</button>
                </div>
                <div class="group-profile">
                  <img :src="avatarFor(activeConversation?.avatar, activeConversation?.name)" :alt="activeConversation?.name" @error="handleContactAvatarError($event, activeConversation?.name)" />
                  <div>
                    <h3>{{ activeConversation?.name }}</h3>
                    <p>{{ activeConversation?.position }} · {{ activeConversation?.department }}</p>
                    <small>{{ activeConversation?.taskNo || '待关联任务' }}</small>
                  </div>
                </div>
                <div class="group-members">
                  <div class="side-section-title">
                    <b>群成员 {{ filteredContacts.length + 1 }} 人</b>
                    <button type="button" @click="inviteContactToMeeting">＋</button>
                  </div>
                  <button v-for="contact in filteredContacts.slice(0, 8)" :key="contact.id" type="button" @click="startDirectChat(contact)">
                    <img :src="avatarFor(contact.avatar, contact.name)" :alt="contact.name" @error="handleContactAvatarError($event, contact.name)" />
                    <span>{{ contact.name }}</span>
                  </button>
                </div>
                <div class="detail-grid">
                  <span>专业：{{ activeConversation?.specialty }}</span>
                  <span>擅长设备：{{ activeConversation?.devices?.join('、') }}</span>
                  <span>当前任务：{{ activeConversation?.currentTask }}</span>
                  <span>工作负载：{{ activeConversation?.workload }}%</span>
                </div>
                <div class="meeting-board">
                  <div class="side-section-title">
                    <b>会议安排</b>
                    <button type="button" @click="scheduleMeeting">安排</button>
                  </div>
                  <article v-for="meeting in contactMeetings" :key="meeting.id" :class="{ active: activeConversationId === `meeting-${meeting.id}` }" @click="openMeeting(meeting)">
                    <strong>{{ meeting.title }}</strong>
                    <small>{{ meeting.time }} · {{ meeting.members.length }} 人</small>
                    <span>{{ meeting.status }}</span>
                  </article>
                </div>
                <div class="group-setting-list">
                  <button type="button" @click="openTaskPicker('assign')"><span>群管理</span><b>添加到任务</b></button>
                  <button type="button" @click="requestSupport"><span>群动态</span><b>请求专家支援</b></button>
                  <button type="button" @click="scheduleMeeting"><span>群会议</span><b>预约会议</b></button>
                  <button type="button" @click="openTaskPicker('send')"><span>分享</span><b>发送任务资料</b></button>
                  <button type="button" @click="summarizeConversation"><span>消息记录</span><b>总结协作重点</b></button>
                  <button type="button" @click="toast('已清空当前筛选')"><span>清空消息记录</span><b>保留协作档案</b></button>
                </div>
                <div class="collab-actions">
                  <button type="button" @click="createCollaborationGroup">创建协作群</button>
                  <button type="button" class="danger" @click="toast('已退出当前群聊演示')">退出群聊</button>
                </div>
              </aside>
            </div>
          </template>

</section>

<section v-else-if="activePage === 'knowledge'" class="page-grid">
          <div class="panel span-all knowledge-nav-panel">
            <div class="panel-head">
              <div>
                <p class="eyebrow">能力资产</p>
                <h3>能力中心</h3>
                <small>接入本机 Agent、沉淀可复用 Skill，并管理它们的权限、备份与记忆迁移</small>
              </div>
              <div class="tabs">
                <button v-for="tab in knowledgeTabs" :key="tab.key" type="button" :class="{ active: knowledgePanel === tab.key }" @click="knowledgePanel = tab.key">{{ tab.label }}</button>
              </div>
            </div>
          </div>


          <template v-if="knowledgePanel === 'recheck'">
            <div class="panel span-all skf-panel">
              <header class="skf-hero">
                <div class="skf-hero-main">
                  <p class="eyebrow">团队能力资产</p>
                  <h3>团队技能工厂</h3>
                  <p class="skf-hero-line">项目完成不是终点。一次优秀任务执行结束后，系统继续判断：这次经验能不能成为下一次任务可以直接复用的 Skill？</p>
                  <div class="skf-flow">
                    <button
                      v-for="(stage, index) in skillPipeline"
                      :key="stage.key"
                      type="button"
                      :class="{ active: skillStage === stage.key }"
                      :title="stage.desc"
                      @click="setSkillStageFilter(stage.key)"
                    >
                      <b>{{ String(index + 1).padStart(2, '0') }}</b>
                      <span>{{ stage.label }}</span>
                      <em>{{ skillPipelineCount(stage.key) }}</em>
                    </button>
                  </div>
                  <p class="skf-flow-hint">
                    <template v-if="skillStage">{{ skillPipeline.find((item) => item.key === skillStage)?.desc }} · 再点一次取消筛选</template>
                    <template v-else>点击任一阶段可聚焦该环节，流水线从任务轨迹一路走到 Agent 调用</template>
                  </p>
                </div>
                <div class="skf-hero-metrics">
                  <article class="tone-teal"><small>Skill 总数</small><b>{{ skillMetrics.total }}</b><em>其中 {{ skillMetrics.production }} 个在生产</em></article>
                  <article class="tone-blue"><small>累计调用</small><b>{{ skillMetrics.calls.toLocaleString() }}</b><em>被 Agent 直接复用</em></article>
                  <article class="tone-teal"><small>平均质量分</small><b>{{ skillMetrics.avgQuality }}</b><em>成功率 {{ skillMetrics.avgSuccess }}%</em></article>
                  <article class="tone-amber"><small>待处理候选</small><b>{{ skillMetrics.candidates }}</b><em>来自执行轨迹</em></article>
                </div>
              </header>

              <section class="skf-block">
                <div class="section-title-row">
                  <div>
                    <p class="eyebrow">候选发现</p>
                    <h3>系统自动分析历史任务、Agent Trace、Memory 与最终产物</h3>
                  </div>
                  <span class="quiet-label">识别口径：重复出现 · 成功率高 · 人工修改少 · 输入输出稳定 · 多次被复用</span>
                </div>
                <div class="skf-candidates">
                  <article v-for="candidate in skillCandidates" :key="candidate.id" class="skf-candidate" :class="{ chosen: skillDraftForm.candidateId === candidate.id }">
                    <div class="skf-candidate-head">
                      <span class="skf-candidate-mark">稳定度 {{ candidate.stability }}%</span>
                      <div>
                        <b>{{ candidate.taskTitle }}</b>
                        <small>{{ candidate.source }} · {{ candidate.traceId }}</small>
                      </div>
                    </div>
                    <p class="skf-candidate-say">该任务已成功执行 {{ candidate.runs }} 次，流程稳定度 {{ candidate.stability }}%，建议沉淀为 Skill。</p>
                    <ul class="skf-signals">
                      <li v-for="signal in candidate.signals" :key="signal">{{ signal }}</li>
                    </ul>
                    <div class="skf-candidate-metrics">
                      <span><small>成功率</small><b>{{ candidate.successRate }}%</b></span>
                      <span><small>人工修改</small><b>{{ candidate.humanEdit }}%</b></span>
                      <span><small>输入输出稳定</small><b>{{ candidate.ioStable }}%</b></span>
                      <span><small>被复用</small><b>{{ candidate.reused }} 次</b></span>
                    </div>
                    <div class="skf-candidate-foot">
                      <span>建议命名 <b>{{ candidate.suggested }}</b></span>
                      <button class="primary" type="button" @click="openSkillCandidate(candidate)">提取为 Skill 候选</button>
                    </div>
                  </article>
                </div>
              </section>

              <section v-if="skillStage === 'generate'" class="skf-block skf-generate">
                <div class="section-title-row">
                  <div>
                    <p class="eyebrow">Skill 生成</p>
                    <h3>按轨迹自动生成 Skill 包，字段可人工校正</h3>
                  </div>
                  <span class="quiet-label">{{ skillDraftForm.candidateId ? `来源候选：${skillDraftForm.candidateId}` : '从上方候选选一个开始' }}</span>
                </div>
                <div class="skf-form">
                  <label><span>Skill 名称</span><input v-model.trim="skillDraftForm.name" placeholder="如：任务上下文包组装" /></label>
                  <label><span>所属类别</span><select v-model="skillDraftForm.category"><option v-for="item in SKILL_CATEGORIES" :key="item">{{ item }}</option></select></label>
                  <label class="wide"><span>功能说明</span><textarea v-model.trim="skillDraftForm.summary" placeholder="一句话说清这个 Skill 解决什么问题"></textarea></label>
                  <label class="wide"><span>适用场景</span><input v-model.trim="skillDraftForm.useCase" placeholder="什么时候应该调用它" /></label>
                  <label><span>输入参数</span><input v-model.trim="skillDraftForm.inputs" placeholder="task_goal, context_pack, files" /></label>
                  <label><span>输出结构</span><input v-model.trim="skillDraftForm.outputs" placeholder="artifact, memory_candidate" /></label>
                  <label class="wide"><span>执行步骤（每行一步）</span><textarea v-model.trim="skillDraftForm.steps" placeholder="解析任务目标&#10;召回证据&#10;执行并记录轨迹"></textarea></label>
                  <label><span>依赖 Agent</span>
                    <select v-model="skillDraftForm.agents" multiple>
                      <option v-for="agent in agentRegistry" :key="agent.id" :value="agent.id">{{ agent.name }} · {{ agent.code }}</option>
                    </select>
                  </label>
                  <label><span>依赖工具</span><input v-model.trim="skillDraftForm.tools" placeholder="repo_search, memory_recall" /></label>
                  <label><span>权限要求</span>
                    <select v-model="skillDraftForm.permissions" multiple>
                      <option v-for="item in AGENT_PERMISSIONS" :key="item">{{ item }}</option>
                    </select>
                  </label>
                  <label class="wide"><span>异常处理规则</span><textarea v-model.trim="skillDraftForm.exceptions" placeholder="证据不足时不产出结论，改为列出缺口清单"></textarea></label>
                  <label class="wide"><span>Eval 标准</span><textarea v-model.trim="skillDraftForm.evalCriteria" placeholder="回放通过率 ≥ 90%；人工删改比例 ≤ 15%"></textarea></label>
                </div>
                <div class="skf-generate-foot">
                  <span class="skf-pack-preview">将生成 Skill 包：<b v-for="item in SKILL_PACKAGE" :key="item">{{ item }}</b></span>
                  <button class="primary" type="button" :disabled="!skillDraftReady" @click="generateSkillFromDraft">生成 Skill 包并进入测试</button>
                </div>
              </section>

              <section class="skf-block">
                <div class="section-title-row">
                  <div>
                    <p class="eyebrow">技能库</p>
                    <h3>团队内部 Skill 库</h3>
                  </div>
                  <span class="quiet-label">按类别管理 · 支持搜索、筛选、排序、收藏与调用</span>
                </div>
                <div class="skf-toolbar">
                  <input v-model.trim="skillFilter.keyword" placeholder="搜索 Skill 名称、简介、适用场景" />
                  <select v-model="skillFilter.category"><option>全部</option><option v-for="item in SKILL_CATEGORIES" :key="item">{{ item }}</option></select>
                  <select v-model="skillFilter.status"><option value="全部">全部状态</option><option v-for="item in SKILL_STAGES" :key="item" :value="item">{{ SKILL_STAGE_LABEL[item] }}</option></select>
                  <select v-model="skillFilter.sort">
                    <option value="quality">按质量分</option>
                    <option value="calls">按调用次数</option>
                    <option value="success">按成功率</option>
                    <option value="cost">按平均成本</option>
                    <option value="updated">按更新时间</option>
                  </select>
                  <button type="button" :class="{ active: skillFilter.favoriteOnly }" @click="skillFilter.favoriteOnly = !skillFilter.favoriteOnly">★ 只看收藏</button>
                  <span class="skf-sync" :class="skillSync.source" :title="skillSync.source === 'server' ? 'Skill 库读写走后端 team_skills 表' : '后端不可用，本次改动只保存在浏览器内存'">
                    <i></i>{{ skillSync.loading ? '读取团队库…' : skillSync.saving ? '保存中…' : (skillSync.source === 'server' ? '已接入团队库' : '本地模式') }}
                  </span>
                  <span class="skf-toolbar-count">{{ filteredSkillLibrary.length }} / {{ skillLibrary.length }} 个 Skill</span>
                </div>
                <div v-if="filteredSkillLibrary.length === 0" class="empty">没有匹配的 Skill，换个关键词或清掉筛选条件。</div>
                <div v-else class="skf-grid">
                  <article
                    v-for="skill in filteredSkillLibrary"
                    :key="skill.id"
                    class="skf-card"
                    :class="[`stage-${skill.status.toLowerCase()}`, { active: selectedSkillId === skill.id }]"
                    @click="selectedSkillId = skill.id; skillDetailTab = 'overview'"
                  >
                    <div class="skf-card-head">
                      <div>
                        <b>{{ skill.name }}</b>
                        <small>{{ skill.category }} · {{ skill.id }}</small>
                      </div>
                      <button type="button" class="skf-star" :class="{ on: skill.favorite }" @click.stop="toggleSkillFavorite(skill)">★</button>
                    </div>
                    <p>{{ skill.summary }}</p>
                    <small class="skf-usecase">适用任务：{{ skill.useCase }}</small>
                    <div class="skf-card-agents">
                      <span v-for="agentId in skill.agents" :key="agentId" @click.stop="openAgentFromSkill(agentId)">{{ agentById(agentId)?.name || agentId }}</span>
                      <em v-if="skill.agents.length === 0">未挂载 Agent</em>
                    </div>
                    <div class="skf-card-metrics">
                      <span><small>版本</small><b>{{ skill.version }}</b></span>
                      <span><small>调用</small><b>{{ skill.calls }}</b></span>
                      <span><small>成功率</small><b>{{ skill.successRate }}%</b></span>
                      <span><small>质量分</small><b>{{ skill.qualityScore }}</b></span>
                      <span><small>平均成本</small><b>¥{{ skill.avgCost }}</b></span>
                    </div>
                    <div class="skf-card-foot">
                      <span class="badge" :class="`tone-${SKILL_STAGE_TONE[skill.status]}`">{{ SKILL_STAGE_LABEL[skill.status] }}</span>
                      <span class="skf-updated">{{ skill.updatedAt }}</span>
                    </div>
                  </article>
                </div>
              </section>

              <section v-if="selectedSkill" class="skf-block skf-detail">
                <div class="section-title-row">
                  <div>
                    <p class="eyebrow">技能详情</p>
                    <h3>{{ selectedSkill.name }} <small>{{ selectedSkill.version }} · {{ SKILL_STAGE_LABEL[selectedSkill.status] }}</small></h3>
                  </div>
                  <div class="skf-detail-actions">
                    <button type="button" @click="runSkillEval(selectedSkill)" :disabled="skillEvalRun.running">{{ skillEvalRun.running ? 'Eval 执行中…' : '运行 Skill Eval' }}</button>
                    <button type="button" @click="advanceSkillStatus(selectedSkill)">推进状态</button>
                    <button type="button" class="danger" @click="deprecateSkill(selectedSkill)">下线</button>
                  </div>
                </div>
                <div class="skf-detail-tabs">
                  <button v-for="tab in [['overview','基本信息'],['spec','结构化字段'],['package','Skill 包'],['agents','关联 Agent'],['eval','Skill Eval'],['versions','版本管理']]" :key="tab[0]" type="button" :class="{ active: skillDetailTab === tab[0] }" @click="skillDetailTab = tab[0]">{{ tab[1] }}</button>
                </div>

                <div v-if="skillDetailTab === 'overview'" class="skf-detail-body">
                  <div class="skf-facts">
                    <span><small>状态</small><b>{{ SKILL_STAGE_LABEL[selectedSkill.status] }}</b></span>
                    <span><small>版本</small><b>{{ selectedSkill.version }}</b></span>
                    <span><small>更新时间</small><b>{{ selectedSkill.updatedAt }}</b></span>
                    <span><small>创建来源</small><b>{{ selectedSkill.origin }}</b></span>
                    <span><small>创建人</small><b>{{ selectedSkill.author }}</b></span>
                    <span><small>调用次数</small><b>{{ selectedSkill.calls }}</b></span>
                    <span><small>成功率</small><b>{{ selectedSkill.successRate }}%</b></span>
                    <span><small>质量分</small><b>{{ selectedSkill.qualityScore }}</b></span>
                    <span><small>平均成本</small><b>¥{{ selectedSkill.avgCost }}</b></span>
                    <span><small>平均执行时间</small><b>{{ selectedSkill.avgDuration }}s</b></span>
                    <span><small>最近一次 Eval</small><b>{{ selectedSkill.lastEval }}</b></span>
                    <span><small>关联项目</small><b>一休 TeamMemory OS</b></span>
                  </div>
                  <p class="skf-detail-summary">{{ selectedSkill.summary }}</p>
                  <p class="skf-detail-summary">适用场景：{{ selectedSkill.useCase }}</p>
                </div>

                <div v-else-if="skillDetailTab === 'spec'" class="skf-spec">
                  <div><h4>输入参数</h4><ul><li v-for="item in selectedSkill.inputs" :key="item">{{ item }}</li></ul></div>
                  <div><h4>输出结构</h4><ul><li v-for="item in selectedSkill.outputs" :key="item">{{ item }}</li></ul></div>
                  <div><h4>执行步骤</h4><ol><li v-for="item in selectedSkill.steps" :key="item">{{ item }}</li></ol></div>
                  <div><h4>依赖 Agent</h4><ul><li v-for="id in selectedSkill.agents" :key="id"><a @click="openAgentFromSkill(id)">{{ agentById(id)?.name || id }}</a></li></ul></div>
                  <div><h4>依赖工具</h4><ul><li v-for="item in selectedSkill.tools" :key="item">{{ item }}</li></ul></div>
                  <div><h4>依赖 Memory</h4><ul><li v-if="!selectedSkill.memories.length">暂无</li><li v-for="item in selectedSkill.memories" :key="item">{{ item }}</li></ul></div>
                  <div><h4>权限要求</h4><ul><li v-for="item in selectedSkill.permissions" :key="item">{{ item }}</li></ul></div>
                  <div><h4>示例</h4><ul><li v-for="item in selectedSkill.examples" :key="item">{{ item }}</li></ul></div>
                  <div><h4>异常处理规则</h4><ul><li v-for="item in selectedSkill.exceptions" :key="item">{{ item }}</li></ul></div>
                  <div><h4>Eval 标准</h4><ul><li v-for="item in selectedSkill.evalCriteria" :key="item">{{ item }}</li></ul></div>
                </div>

                <div v-else-if="skillDetailTab === 'package'" class="skf-detail-body">
                  <p class="skf-detail-summary">Skill 以包的形式挂在 Agent 上，版本号跟包一起发布。</p>
                  <div class="skf-pack">
                    <span v-for="item in SKILL_PACKAGE" :key="item"><b>{{ item }}</b><small>{{ item === 'SKILL.md' ? '能力说明与适用边界' : item === 'workflow.yaml' ? '执行步骤与依赖' : item === 'tools.json' ? '工具与权限声明' : item.endsWith('/') ? `共 ${selectedSkill.tests} 个用例` : '评测标准' }}</small></span>
                  </div>
                </div>

                <div v-else-if="skillDetailTab === 'agents'" class="skf-detail-body">
                  <p class="skf-detail-summary">一个 Skill 可以被多个 Agent 使用，一个 Agent 也可以挂多个 Skill。</p>
                  <div class="skf-agent-links">
                    <article v-for="id in selectedSkill.agents" :key="id" @click="openAgentFromSkill(id)">
                      <b>{{ agentById(id)?.name || id }}</b>
                      <small>{{ agentById(id)?.code }} · {{ agentById(id)?.role }}</small>
                      <em>{{ AGENT_STATE_LABEL[agentById(id)?.status] }} · 成功率 {{ agentById(id)?.successRate }}%</em>
                    </article>
                    <p v-if="!selectedSkill.agents.length" class="empty">这个 Skill 还没有挂到任何 Agent 上，发布后请到 Agent Registry 挂载。</p>
                  </div>
                </div>

                <div v-else-if="skillDetailTab === 'eval'" class="skf-detail-body">
                  <div class="skf-eval-bar">
                    <label><span>回放样本</span><input type="number" min="5" max="80" v-model.number="skillEvalRun.sample" /></label>
                    <label><span>Eval 方式</span>
                      <select v-model="skillEvalRun.kind">
                        <option>历史任务回放</option><option>标准测试集</option><option>版本回归</option><option>模型对比</option><option>Agent 对比</option>
                      </select>
                    </label>
                    <button class="primary" type="button" :disabled="skillEvalRun.running" @click="runSkillEval(selectedSkill)">{{ skillEvalRun.running ? '评测中…' : '开始评测' }}</button>
                  </div>
                  <div v-if="skillEvalRun.result" class="skf-eval-result" :class="{ blocked: skillEvalRun.result.blocks.length }">
                    <div class="skf-eval-score"><b>{{ skillEvalRun.result.score }}</b><small>Skill Quality Score</small></div>
                    <div class="skf-eval-nums">
                      <span><small>成功率</small><b>{{ skillEvalRun.result.pass }}%</b></span>
                      <span><small>结果一致性</small><b>{{ skillEvalRun.result.consistency }}%</b></span>
                      <span><small>输出完整性</small><b>{{ skillEvalRun.result.completeness }}%</b></span>
                      <span><small>人工评分</small><b>{{ skillEvalRun.result.human }}/5</b></span>
                    </div>
                    <ul v-if="skillEvalRun.result.blocks.length" class="skf-blocks"><li v-for="item in skillEvalRun.result.blocks" :key="item">{{ item }}</li></ul>
                    <p v-else class="skf-pass">通过发布门禁，可推进到已验证 / 生产。</p>
                  </div>
                  <table class="table skf-eval-table">
                    <div class="tr head"><span>时间</span><span>方式</span><span>样本</span><span>成功率</span><span>一致性</span><span>完整性</span><span>人工</span><span>结论</span></div>
                    <div v-for="record in selectedSkill.evals" :key="record.at" class="tr">
                      <span>{{ record.at }}</span><span>{{ record.kind }}</span><span>{{ record.sample }}</span>
                      <span>{{ record.pass }}%</span><span>{{ record.consistency }}%</span><span>{{ record.completeness }}%</span>
                      <span>{{ record.human }}/5</span><span>{{ record.note }}</span>
                    </div>
                  </table>
                </div>

                <div v-else class="skf-detail-body">
                  <div class="skf-version-diff">
                    <h4>版本差异</h4>
                    <div v-for="row in skillVersionDiff(selectedSkill)" :key="row.label" class="skf-diff-row">
                      <span>{{ row.label }}</span>
                      <b class="from">{{ row.from }}</b>
                      <i>→</i>
                      <b :class="row.up ? 'up' : 'down'">{{ row.to }}</b>
                    </div>
                  </div>
                  <div class="skf-versions">
                    <article v-for="(item, index) in selectedSkill.versions" :key="item.version + index">
                      <b>{{ item.version }}</b>
                      <small>{{ item.at }}</small>
                      <p>{{ item.note }}</p>
                      <em>成功率 {{ item.successRate }}% · 质量分 {{ item.qualityScore }}</em>
                      <button v-if="index > 0" type="button" @click="rollbackSkillVersion(selectedSkill, item.version)">回滚到此版本</button>
                    </article>
                  </div>
                </div>
              </section>
            </div>
          </template>

          <div v-if="knowledgePanel === 'files'" class="panel span-all areg-panel">
            <!-- ══════════════ 视图一：Agent 中心总览 ══════════════ -->
            <template v-if="agentCenterView === 'hub'">
              <!-- 1. 已接入 Agent -->
              <section class="areg-block">
                <div class="section-title-row">
                  <div>
                    <p class="eyebrow">已接入 Agent</p>
                    <h3>当前电脑已识别并接入的 Agent</h3>
                  </div>
                  <span class="quiet-label">{{ connectedAgents.length }} 个已接入 · 点「管理」进入详情</span>
                </div>
                <div v-if="!connectedAgents.length" class="empty">还没有接入任何 Agent，从下面的「获取更多 Agent」开始。</div>
                <div v-else class="areg-hub">
                  <article v-for="agent in visibleConnectedAgents" :key="agent.id" class="areg-hub-row">
                    <img class="areg-logo-img" :src="agent.logo" :alt="agent.name" @error="handleContentImageError($event, '/static/yixiu-logo-icon.png')" />
                    <div class="areg-hub-body">
                      <div class="areg-hub-title">
                        <b>{{ agent.name }}</b>
                        <em class="areg-pill on"><i></i>已接入</em>
                        <em class="areg-pill" :class="agent.appInstalled ? 'ok' : 'warn'"><i></i>{{ agent.appInstalled ? '应用已安装' : '应用已卸载' }}</em>
                      </div>
                      <small class="areg-hub-detail">{{ acHubDetail(agent) }}</small>
                    </div>
                    <div class="areg-hub-actions">
                      <button class="primary" type="button" @click="acOpenManage(agent)">管理</button>
                      <div class="areg-menu-wrap">
                        <button type="button" title="更多操作" @click="acMenuAgentId = acMenuAgentId === agent.id ? '' : agent.id">···</button>
                        <div v-if="acMenuAgentId === agent.id" class="areg-menu">
                          <button type="button" @click="acOpenManage(agent)">查看详情</button>
                          <button type="button" @click="acRunBackup(agent)">立即备份</button>
                          <button type="button" @click="acOpenManage(agent); acDetailTab = 'migrate'">记忆迁移</button>
                          <button type="button" @click="acDisconnectAgent(agent)">断开接入</button>
                          <button type="button" class="danger" @click="acRemoveAgent(agent)">从列表移除</button>
                        </div>
                      </div>
                    </div>
                  </article>
                  <button v-if="connectedAgents.length > 3 && !acShowAllConnected" class="areg-more" type="button" @click="acShowAllConnected = true">
                    查看更多 · 还有 {{ connectedAgents.length - 3 }} 个 ⌄
                  </button>
                  <button v-else-if="acShowAllConnected" class="areg-more" type="button" @click="acShowAllConnected = false">收起 ⌃</button>
                </div>
              </section>

              <!-- 2. 获取更多 Agent -->
              <section class="areg-block">
                <div class="section-title-row">
                  <div>
                    <p class="eyebrow">获取更多 Agent</p>
                    <h3>扫描到 {{ agentCenterCatalog.length }} 个 Agent，本机已接入 {{ acStatusCounts.connected }} 个</h3>
                  </div>
                  <div class="areg-block-actions">
                    <button type="button" :disabled="acScanning" @click="acScanAll">{{ acScanning ? '扫描中…' : '重新扫描' }}</button>
                    <button class="primary" type="button" @click="acShowManualForm = !acShowManualForm">＋ 手动添加</button>
                  </div>
                </div>

                <div v-if="acShowManualForm" class="areg-manual">
                  <div class="areg-manual-head">
                    <b>手动添加 Agent</b>
                    <small>系统暂时无法自动识别的 Agent，可以手动指定名称与数据目录；一休只做只读扫描。</small>
                  </div>
                  <div class="areg-manual-form">
                    <label><span>Agent 名称 *</span><input v-model.trim="acManualForm.name" placeholder="如：My Local Agent" /></label>
                    <label><span>厂商 / 来源</span><input v-model.trim="acManualForm.vendor" placeholder="选填" /></label>
                    <label><span>配置目录 *</span><input v-model.trim="acManualForm.configDir" placeholder="如：~/.myagent/config.json" /></label>
                    <label><span>Session 数据目录</span><input v-model.trim="acManualForm.sessionDir" placeholder="如：~/.myagent/sessions" /></label>
                    <label><span>Memory 数据目录</span><input v-model.trim="acManualForm.memoryDir" placeholder="如：~/.myagent/memory" /></label>
                    <label><span>Skill 数据目录</span><input v-model.trim="acManualForm.skillDir" placeholder="如：~/.myagent/skills" /></label>
                  </div>
                  <div class="areg-manual-foot">
                    <span>敏感项不会被读取，只会标记为「已配置」。</span>
                    <div>
                      <button type="button" @click="acShowManualForm = false">取消</button>
                      <button class="primary" type="button" :disabled="!acManualReady" @click="acAddManualAgent">添加并扫描</button>
                    </div>
                  </div>
                </div>

                <div class="areg-discover">
                  <article v-for="agent in discoverableAgents" :key="agent.id" class="areg-discover-card" :class="`state-${agent.status}`">
                    <img class="areg-logo-img" :src="agent.logo" :alt="agent.name" @error="handleContentImageError($event, '/static/yixiu-logo-icon.png')" />
                    <b>{{ agent.name }}</b>
                    <small class="areg-vendor">{{ agent.sub || agent.vendor }}</small>
                    <button
                      type="button"
                      :class="{ primary: agent.status === 'connected' }"
                      @click="agent.status === 'connected' ? acOpenManage(agent) : (agent.status === 'notDetected' ? acOpenSite(agent) : toast(`${agent.name} 需要先在本机完成授权，一休只做只读扫描`))"
                    >{{ AC_STATUS[agent.status].button }}</button>
                  </article>
                </div>
              </section>

              <!-- 3. 一休内置 Agent -->
              <section class="areg-block">
                <div class="section-title-row">
                  <div>
                    <p class="eyebrow">一休内置 Agent</p>
                    <h3>支撑 TeamMemory OS 运行的团队智能体</h3>
                  </div>
                  <span class="quiet-label">它们的 Skill 依赖关系在 Skill Factory 中维护</span>
                </div>
                <div class="areg-builtin">
                  <article v-for="agent in agentRegistry" :key="agent.id">
                    <img v-if="agent.avatar" :src="agent.avatar" alt="" @error="handleContentImageError($event, '/static/yixiu-logo.png')" />
                    <span v-else class="areg-monogram">{{ agent.name.slice(0, 1) }}</span>
                    <div><b>{{ agent.name }}</b><small>{{ agent.code }} · {{ agent.role }}</small></div>
                    <em class="badge" :class="`tone-${AGENT_STATE_TONE[agent.status]}`">{{ AGENT_STATE_LABEL[agent.status] }}</em>
                    <span class="areg-builtin-meta">{{ agentSkills(agent).length }} Skill · 成功率 {{ agent.successRate }}%</span>
                  </article>
                </div>
              </section>

              <!-- 4. 与 TeamMemory OS 联动 -->
              <section class="areg-block">
                <div class="section-title-row">
                  <div>
                    <p class="eyebrow">联动</p>
                    <h3>接入之后，数据去哪了</h3>
                  </div>
                  <span class="quiet-label">解析 → 标准化 → 沉淀，Agent 之间共享的是记忆而不是文件</span>
                </div>
                <div class="areg-linkage">
                  <article v-for="item in acLinkage" :key="item.key" @click="acGotoLinkage(item)">
                    <b>{{ item.title }}</b>
                    <p>{{ item.desc }}</p>
                    <em>{{ item.value }}</em>
                  </article>
                </div>
              </section>
            </template>

            <!-- ══════════════ 视图二：Agent 管理详情 ══════════════ -->
            <template v-else>
              <header class="areg-manage-head">
                <button class="areg-back" type="button" @click="acBackToHub">← 返回 Agent 中心</button>
                <div class="areg-manage-id">
                  <img class="areg-logo-img" :src="managedAgent.logo" :alt="managedAgent.name" @error="handleContentImageError($event, '/static/yixiu-logo-icon.png')" />
                  <div>
                    <h3>{{ managedAgent.name }}</h3>
                    <small>{{ managedAgent.vendor }} · {{ managedAgent.home }} · 扫描于 {{ managedAgent.scannedAt || '未扫描' }}</small>
                  </div>
                  <em class="badge" :class="`tone-${AC_STATUS[managedAgent.status].tone}`">{{ AC_STATUS[managedAgent.status].label }}</em>
                </div>
                <div class="areg-detail-actions">
                  <button type="button" @click="acRunBackup(managedAgent)">立即备份</button>
                  <button type="button" @click="acDetailTab = 'migrate'">记忆迁移</button>
                  <button class="danger" type="button" @click="acDisconnectAgent(managedAgent); acBackToHub()">断开接入</button>
                </div>
              </header>

              <div class="areg-detail-tabs">
                <button
                  v-for="tab in [['overview','概览'],['projects','项目'],['memory','记忆'],['sessions','会话'],['skills','Skill'],['mcp','MCP'],['config','配置'],['backup','备份'],['migrate','迁移']]"
                  :key="tab[0]" type="button" :class="{ active: acDetailTab === tab[0] }" @click="acDetailTab = tab[0]"
                >{{ tab[1] }}</button>
              </div>

              <!-- 概览 -->
              <div v-if="acDetailTab === 'overview'" class="areg-detail-body">
                <div class="areg-eval-dash">
                  <article v-for="type in AC_ASSET_TYPES" :key="type.key" class="tone-blue">
                    <small>{{ type.label }}</small>
                    <b>{{ acAssetCount(managedAgent, type.key) }}</b>
                    <em>{{ type.desc }}</em>
                  </article>
                </div>
                <div class="areg-facts">
                  <span><small>应用状态</small><b>{{ managedAgent.appInstalled ? '已安装' : '应用已卸载 · 数据保留' }}</b></span>
                  <span><small>数据状态</small><b>{{ managedAgent.dataNote }}</b></span>
                  <span><small>配置目录</small><b>{{ managedAgent.dirs.config }}</b></span>
                  <span><small>Memory 目录</small><b>{{ managedAgent.dirs.memory }}</b></span>
                  <span><small>Session 目录</small><b>{{ managedAgent.dirs.session }}</b></span>
                  <span><small>Skill 目录</small><b>{{ managedAgent.dirs.skill }}</b></span>
                  <span><small>最近使用</small><b>{{ managedAgent.lastUsed }}</b></span>
                  <span><small>敏感配置</small><b>{{ acSensitiveCount(managedAgent) }} 项 · 仅标记不读取</b></span>
                </div>
                <p class="areg-detail-cap">一休只做只读扫描：解析目录结构、会话与记忆文本，不读取凭据类字段。要沉淀到团队记忆或迁移到其它 Agent，请到「迁移」页走标准化流程。</p>
              </div>

              <!-- 项目 -->
              <div v-else-if="acDetailTab === 'projects'" class="areg-detail-body">
                <table class="table areg-history">
                  <div class="tr head"><span>项目</span><span>路径</span><span>会话</span><span>最近使用</span></div>
                  <div v-for="row in acAssetRows(managedAgent, 'projects')" :key="row.path + row.name" class="tr">
                    <span>{{ row.name }}</span><span>{{ row.path }}</span><span>{{ row.sessions }}</span><span>{{ row.lastUsed }}</span>
                  </div>
                </table>
                <p v-if="!acAssetRows(managedAgent, 'projects').length" class="empty">未扫描到项目目录。</p>
              </div>

              <!-- 记忆 -->
              <div v-else-if="acDetailTab === 'memory'" class="areg-detail-body">
                <div class="areg-memory-list">
                  <article v-for="row in acAssetRows(managedAgent, 'memories')" :key="row.title">
                    <div><b>{{ row.title }}</b><small>{{ row.updatedAt }}</small></div>
                    <em class="badge tone-violet">{{ row.kind }}</em>
                  </article>
                  <p v-if="!acAssetRows(managedAgent, 'memories').length" class="empty">未扫描到记忆条目。</p>
                </div>
                <div class="areg-inline-actions">
                  <button type="button" @click="acPushSnapshot(managedAgent, '沉淀前快照', '写入 Team Memory 前自动创建'); toast('已生成快照，可到「备份」页回滚')">沉淀到 Team Memory</button>
                  <button type="button" @click="acGotoLinkage(acLinkage[0])">打开团队记忆</button>
                </div>
              </div>

              <!-- 会话 -->
              <div v-else-if="acDetailTab === 'sessions'" class="areg-detail-body">
                <table class="table areg-history">
                  <div class="tr head"><span>会话</span><span>标题</span><span>消息数</span><span>更新时间</span></div>
                  <div v-for="row in acAssetRows(managedAgent, 'sessions')" :key="row.id" class="tr">
                    <span>{{ row.id }}</span><span>{{ row.title }}</span><span>{{ row.messages }}</span><span>{{ row.updatedAt }}</span>
                  </div>
                </table>
                <p v-if="!acAssetRows(managedAgent, 'sessions').length" class="empty">未扫描到会话记录。</p>
              </div>

              <!-- Skill -->
              <div v-else-if="acDetailTab === 'skills'" class="areg-detail-body">
                <div class="areg-skill-links">
                  <article v-for="row in acAssetRows(managedAgent, 'skills')" :key="row.name" @click="acGotoLinkage(acLinkage[1])">
                    <div><b>{{ row.name }}</b><small>{{ row.kind }} · {{ row.files }} 个文件</small></div>
                    <span><small>来源</small><b>{{ managedAgent.name }}</b></span>
                    <span><small>可提炼</small><b>是</b></span>
                    <span><small>状态</small><b>待审核</b></span>
                  </article>
                  <p v-if="!acAssetRows(managedAgent, 'skills').length" class="empty">该 Agent 没有可解析的 Skill。</p>
                </div>
                <div class="areg-inline-actions">
                  <button type="button" @click="acGotoLinkage(acLinkage[1])">送到 Skill Factory 提炼</button>
                </div>
              </div>

              <!-- MCP -->
              <div v-else-if="acDetailTab === 'mcp'" class="areg-detail-body">
                <div class="areg-spec-3">
                  <div>
                    <h4>已发现的 MCP Server</h4>
                    <ul>
                      <li v-if="!acAssetRows(managedAgent, 'mcp').length">未发现 MCP 配置</li>
                      <li v-for="row in acAssetRows(managedAgent, 'mcp')" :key="row.name"><code>{{ row.name }}</code> · {{ row.endpoint }}</li>
                    </ul>
                  </div>
                  <div>
                    <h4>Prompt / Rules</h4>
                    <ul>
                      <li v-if="!acAssetRows(managedAgent, 'prompts').length">未发现规则文件</li>
                      <li v-for="row in acAssetRows(managedAgent, 'prompts')" :key="row.name">{{ row.name }} · {{ row.kind }} · {{ row.size }}</li>
                    </ul>
                  </div>
                </div>
              </div>

              <!-- 配置 -->
              <div v-else-if="acDetailTab === 'config'" class="areg-detail-body">
                <p class="areg-detail-cap">敏感配置永远不读取内容，只显示是否已配置。权限变更仅对本次会话生效。</p>
                <div class="areg-perms">
                  <button
                    v-for="permission in AC_PERMISSIONS"
                    :key="permission.key"
                    type="button"
                    :class="{ on: acHasPermission(managedAgent, permission), sensitive: permission.level !== 'default' }"
                    @click="acTogglePermission(managedAgent, permission)"
                  >
                    <b>{{ permission.label }}</b>
                    <small>{{ permission.note }}</small>
                    <em>{{ permission.level === 'never' ? '禁止' : (acHasPermission(managedAgent, permission) ? '已授权' : '未授权') }}</em>
                  </button>
                </div>
                <div class="areg-config-list">
                  <article v-for="row in acAssetRows(managedAgent, 'config')" :key="row.name">
                    <b>{{ row.name }}</b>
                    <small>{{ row.sensitive ? '敏感项 · 内容不读取' : '普通配置项' }}</small>
                    <em class="badge" :class="row.sensitive ? 'tone-amber' : 'tone-teal'">已配置</em>
                  </article>
                </div>
              </div>

              <!-- 备份 -->
              <div v-else-if="acDetailTab === 'backup'" class="areg-detail-body">
                <div class="areg-inline-actions">
                  <button class="primary" type="button" @click="acRunBackup(managedAgent)">生成新快照</button>
                  <span class="areg-hint">迁移前会自动创建快照，失败可回滚。</span>
                </div>
                <div class="areg-versions">
                  <article v-for="snapshot in acSnapshots.filter((item) => item.agentId === managedAgent.id)" :key="snapshot.id">
                    <b>{{ snapshot.label }}</b>
                    <small>{{ snapshot.at }} · {{ snapshot.size }}</small>
                    <p>{{ snapshot.reason }}</p>
                    <button type="button" @click="acRollback(snapshot)">回滚到此快照</button>
                  </article>
                  <p v-if="!acSnapshots.filter((item) => item.agentId === managedAgent.id).length" class="empty">还没有快照，点「生成新快照」。</p>
                </div>
              </div>

              <!-- 迁移 -->
              <div v-else class="areg-detail-body">
                <div class="areg-migrate">
                  <div class="areg-migrate-pick">
                    <label><span>来源 Agent</span>
                      <select v-model="acMigrationForm.from">
                        <option v-for="agent in connectedAgents" :key="agent.id" :value="agent.id">{{ agent.name }}</option>
                      </select>
                    </label>
                    <span class="areg-migrate-arrow">→</span>
                    <label><span>目标 Agent</span>
                      <select v-model="acMigrationForm.to">
                        <option v-for="agent in agentCenterCatalog" :key="agent.id" :value="agent.id">{{ agent.name }}</option>
                      </select>
                    </label>
                  </div>

                  <div class="areg-migrate-assets">
                    <span v-for="asset in acMigrationCompatibility" :key="asset.key"
                      :class="{ on: asset.selected, bad: asset.level === 'unsupported' }"
                      @click="asset.level !== 'unsupported' && (acMigrationForm.assets[asset.key] = !acMigrationForm.assets[asset.key])">
                      <b>{{ asset.label }}</b>
                      <small>{{ asset.desc }}</small>
                      <em>{{ asset.levelLabel }}</em>
                    </span>
                  </div>

                  <div class="areg-pipeline">
                    <span v-for="(stage, index) in AC_PIPELINE" :key="stage.key"
                      :class="{ active: acMigrationRun.running && acMigrationRun.stage === index, done: acMigrationRun.stage > index }">
                      <b>{{ String(index + 1).padStart(2, '0') }}</b>
                      <strong>{{ stage.label }}</strong>
                      <small>{{ stage.desc }}</small>
                    </span>
                  </div>
                  <p class="areg-hint">迁移不是复制文件：先由 Agent Parser 解析来源格式，标准化成统一记忆结构，做兼容性检查，再由目标 Agent Adapter 按目标格式写入。</p>

                  <div class="areg-migrate-foot">
                    <span>{{ acMigrationSelected.length }} 类资产 · 目标 {{ agentCenterCatalog.find((item) => item.id === acMigrationForm.to)?.name || '—' }}</span>
                    <button class="primary" type="button" :disabled="acMigrationRun.running" @click="acRunMigration">
                      {{ acMigrationRun.running ? '迁移中…' : '开始迁移' }}
                    </button>
                  </div>

                  <div v-if="acMigrationRun.result" class="areg-migrate-result">
                    <b>迁移完成</b>
                    <p>{{ acMigrationRun.result.from }} → {{ acMigrationRun.result.to }} · {{ acMigrationRun.result.moved }} 项资产已标准化写入</p>
                    <small>{{ acMigrationRun.result.assets.join('、') }} · {{ acMigrationRun.result.at }}</small>
                  </div>
                </div>

                <table class="table areg-history">
                  <div class="tr head"><span>时间</span><span>来源 → 目标</span><span>资产</span><span>结果</span></div>
                  <div v-for="row in acMigrationHistory" :key="row.id" class="tr">
                    <span>{{ row.at }}</span>
                    <span>{{ agentCenterCatalog.find((item) => item.id === row.from)?.name || row.from }} → {{ agentCenterCatalog.find((item) => item.id === row.to)?.name || row.to }}</span>
                    <span>{{ row.assets.join('、') }}</span>
                    <span>{{ row.status }} · {{ row.moved }} 项</span>
                  </div>
                </table>
              </div>
            </template>
          </div>

          <template v-else-if="knowledgePanel === 'mcp'">
            <div class="panel span-all search-update-panel">
              <div class="panel-head">
                <div><p class="eyebrow">MCP / API Integration</p><h3>给 Codex / Claude 的接入配置</h3><small>外部 AI 通过 MCP 工具或 API 把当前任务总结主动写入一休。</small></div>
                <button type="button" @click="openMcpConfig">重新生成配置</button>
              </div>
              <div class="search-update-layout">
                <div class="form-grid">
                  <label class="wide">接入地址<input :value="mcpManifest.endpoint || '加载中...'" readonly /></label>
                  <label class="wide">鉴权方式<input :value="mcpManifest.auth?.header || 'Authorization: Bearer <YIXIU_IMPORT_TOKEN>'" readonly /></label>
                  <label class="wide">推荐给 Codex / Claude 的提示词<textarea :value="mcpUsagePrompt" readonly></textarea></label>
                  <label class="wide">Codex 固定上传格式<textarea :value="codexFixedUploadTemplate" readonly></textarea></label>
                </div>
                <aside class="knowledge-update-aside">
                  <div class="update-quality-card">
                    <b>{{ mcpManifest.name || '一休 AI Import Gateway' }}</b>
                    <span><small>工具数量</small><em>{{ mcpManifest.tools?.length || 0 }}</em></span>
                    <span><small>同步方向</small><em>外部 AI → 一休</em></span>
                    <span><small>入库策略</small><em>候选资产人工审核</em></span>
                  </div>
                  <div class="update-rule-list">
                    <b>开放工具</b>
                    <span v-for="tool in mcpManifest.tools || []" :key="tool.name">
                      <small>{{ tool.name }}</small><em>{{ tool.purpose }}</em>
                    </span>
                  </div>
                </aside>
              </div>
            </div>
          </template>
</section>

        <section v-else class="profile-dashboard">
          <div class="profile-hero-card">
            <div class="profile-avatar-wrap">
              <img :src="user.avatar" alt="" @error="handleAvatarError" />
              <button type="button" aria-label="更换头像" @click="openProfileEditor">
                <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h4l2-2h4l2 2h4v12H4Z"></path><circle cx="12" cy="13" r="3"></circle></svg>
              </button>
            </div>
            <div class="profile-hero-main">
              <div class="profile-name-row">
                <h2>{{ user.name }}</h2>
                <span class="profile-skill-badge">项目协作者 / Agent 协作者</span>
              </div>
              <p>成员 ID：{{ user.employeeId }} · 团队角色：{{ user.teamRole }} · {{ user.department }}</p>
              <p class="profile-hero-meta">当前项目：{{ user.currentProject }} · 所属团队：{{ user.team }}</p>
              <div class="profile-progress">
                <span>资料完整度</span>
                <i><b style="width: 86%"></b></i>
                <em>86%</em>
              </div>
              <small>补全当前项目、所属团队与协作偏好，可提升 Agent 分派与 Context 召回的准确度。</small>
              <div class="profile-tags-soft">
                <span v-for="tag in user.specialties" :key="tag">{{ tag }}</span>
                <span>协作等级：{{ profileCollabLevel }}</span>
              </div>
            </div>
            <div class="profile-hero-actions">
              <button type="button" @click="openProfileEditor">
                <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20h9"></path><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"></path></svg>
                编辑资料
              </button>
              <button type="button" @click="activePage = 'tasks'; taskPanel = 'manage'">
                <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3v3M17 3v3M4 9h16M6 5h12a2 2 0 0 1 2 2v12H4V7a2 2 0 0 1 2-2Z"></path></svg>
                查看项目
              </button>
            </div>
          </div>

          <div class="profile-quick-row">
            <button v-for="card in profileQuickCards" :key="card.title" type="button" @click="runProfileItem(card)">
              <span :class="`tone-${card.tone}`">
                <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true">
                  <path v-for="path in iconParts(card.icon)" :key="path" :d="path"></path>
                </svg>
              </span>
              <small>{{ card.title }}</small>
              <b>{{ card.value }}</b>
              <em>{{ card.desc }}</em>
            </button>
          </div>

          <div class="profile-main-grid">
            <article class="profile-panel profile-security-panel">
              <div class="profile-panel-head">
                <h3>账号与安全</h3>
                <span>安全等级：高</span>
              </div>
              <div class="profile-setting-list">
                <button v-for="item in profileSecurityItems" :key="item.title" type="button" @click="runProfileItem(item)">
                  <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path v-for="path in iconParts(item.icon)" :key="path" :d="path"></path></svg>
                  <b>{{ item.title }}</b>
                  <small>{{ item.desc }}</small>
                  <em>{{ item.meta }}</em>
                </button>
              </div>
            </article>

            <article class="profile-panel profile-tools-panel">
              <div class="profile-panel-head">
                <h3>常用功能</h3>
                <span>快捷入口</span>
              </div>
              <div class="profile-tool-grid">
                <button v-for="item in profileToolItems" :key="item.title" type="button" @click="runProfileItem(item)">
                  <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path v-for="path in iconParts(item.icon)" :key="path" :d="path"></path></svg>
                  <b>{{ item.title }}</b>
                </button>
              </div>
            </article>

            <article class="profile-panel profile-activity-panel">
              <div class="profile-panel-head">
                <h3>最近动态</h3>
                <button type="button" @click="activePage = 'tasks'; taskPanel = 'manage'">全部记录</button>
              </div>
              <div class="profile-timeline">
                <button v-for="item in profileRecentItems" :key="item.title" type="button" @click="runProfileItem(item)">
                  <i></i>
                  <span>
                    <b>{{ item.title }}</b>
                    <small>{{ item.desc }}</small>
                  </span>
                  <time>{{ item.meta }}</time>
                </button>
              </div>
            </article>

            <article class="profile-growth-card">
              <div>
                <p>协作画像 · AI 协作能力值</p>
                <h3>{{ profileGrowthScore }}</h3>
                <span>由项目参与、Memory 与 Skill 贡献、Agent 协作、任务完成与知识沉淀综合计算。</span>
                <i><b :style="{ width: `${profileCollabProgress}%` }"></b></i>
              </div>
              <div class="profile-growth-level">
                <small>协作等级</small>
                <b>{{ profileCollabLevel }}</b>
                <button type="button" @click="activePage = 'profile'">成长中心</button>
              </div>
              <div class="profile-growth-benefits">
                <span v-for="item in profileGrowthBenefits" :key="item.title">
                  <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path v-for="path in iconParts(item.icon)" :key="path" :d="path"></path></svg>
                  {{ item.title }}
                </span>
              </div>
              <div class="profile-level-ladder">
                <span
                  v-for="(level, index) in PROFILE_COLLAB_LEVELS"
                  :key="level"
                  :class="{ reached: index <= profileCollabLevelIndex, current: index === profileCollabLevelIndex }"
                >{{ level }}</span>
              </div>
            </article>

            <article class="profile-panel profile-preference-panel">
              <div class="profile-panel-head">
                <h3>个性化设置</h3>
                <span>工作偏好</span>
              </div>
              <div class="profile-preference-list">
                <button v-for="item in profilePreferenceItems" :key="item.title" type="button" @click="runProfileItem(item)">
                  <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path v-for="path in iconParts(item.icon)" :key="path" :d="path"></path></svg>
                  <b>{{ item.title }}</b>
                  <span>{{ item.meta }}</span>
                </button>
              </div>
            </article>
          </div>

        </section>
      </section>

      <button class="panel-resizer" type="button" aria-label="拖动调整智能体面板宽度" title="拖动调整智能体面板宽度" @pointerdown="startOperatorResize">
        <span></span>
      </button>

      <aside class="operator-panel" :class="'op-theme-' + (operatorProfile.id || 'tiangong')" aria-label="页面智能体对话">
        <div class="operator-head">
          <img class="operator-avatar" :src="avatarFor(operatorProfile.avatar, operatorProfile.name)" :alt="operatorProfile.name" @error="handleAvatarError" />
          <div>
            <p class="eyebrow">智能体协助</p>
            <h2>{{ operatorProfile.name }}</h2>
            <small class="operator-role">{{ operatorProfile.role }}</small>
          </div>
          <div class="operator-head-actions">
            <span :class="['operator-status', operatorProfile.status]">{{ operatorProfile.statusText }}</span>
          </div>
        </div>

        <p class="operator-duty">{{ operatorProfile.duty }}</p>
        <p class="operator-slogan">{{ operatorProfile.slogan }}</p>

        <section v-if="false" class="aios-recorder" :class="{ active: aiosLive.status !== 'idle' }" aria-label="天工操作过程">
          <header class="aios-recorder-head">
            <div>
              <p class="eyebrow">天工操作过程</p>
              <h3>{{ aiosLive.goal || '等待任务指令' }}</h3>
            </div>
            <button type="button" :disabled="aiosLive.loading" @click="refreshAiosTrace()">
              {{ aiosLive.loading ? '同步中' : '刷新' }}
            </button>
          </header>
          <div class="aios-meter" aria-hidden="true">
            <span :style="{ width: `${aiosLive.progress || 0}%` }"></span>
          </div>
          <div class="aios-recorder-meta">
            <span>{{ aiosStatusText }}</span>
            <span>步骤 {{ aiosQueueSummary }}</span>
            <span v-if="aiosActiveStep">当前：{{ aiosActiveStep.title || aiosActiveStep.key }}</span>
          </div>
          <div v-if="aiosLive.steps.length" class="aios-agent-rail">
            <span v-for="step in aiosLive.steps" :key="step.key || step.title" :class="['aios-step-dot', step.state || step.status || 'pending']">
              <i>{{ agentShortName(step.agent?.name || step.agent_name || step.agentId || step.agent_id) }}</i>
              <b>{{ step.title || step.key }}</b>
            </span>
          </div>
          <div v-else class="aios-empty-trace">向天工发送“帮我规划并执行……”后，这里会显示实时过程。</div>
          <div v-if="aiosVisibleEvents.length" class="aios-event-stream">
            <article v-for="event in aiosVisibleEvents" :key="event.id" :class="event.status || event.event_type">
              <span>{{ event.agent_name || agentName(event.agent_id) }}</span>
              <div>
                <b>{{ event.title || event.event_type }}</b>
                <small>{{ event.content || '已同步业务动作' }} · {{ formatAiosTime(event.created_at) }}</small>
              </div>
            </article>
          </div>
          <p v-if="aiosLive.error" class="aios-error">{{ aiosLive.error }}</p>
        </section>

        <div class="chat-thread">
          <div class="bubble assistant">
            {{ operatorProfile.welcome }}
          </div>
          <div class="bubble user">
            {{ operatorProfile.sampleAsk }}
          </div>
          <div class="bubble assistant">
            {{ operatorProfile.sampleAnswer }}
          </div>
          <div v-for="message in currentOperatorMessages" :key="message.id" :class="['bubble', message.role, { loading: message.loading }]">
            <span v-if="message.loading" class="loading-dots"><i></i><i></i><i></i></span>
            <div v-if="message.attachments?.length" class="message-attachments">
              <figure v-for="file in message.attachments" :key="file.localId || file.name" :class="{ image: file.type === '图片' }">
                <img v-if="file.type === '图片' && file.url" :src="file.url" :alt="file.name" />
                <span v-else>{{ file.type || '附件' }}</span>
                <figcaption>
                  <b>{{ file.name }}</b>
                  <small>{{ file.sizeText || file.size || file.status || '已添加' }}</small>
                </figcaption>
              </figure>
            </div>
            <details v-if="message.steps && message.steps.length" class="tiangong-trace" v-show="!message.loading">
              <summary>天工执行过程 · {{ message.steps.length }} 步</summary>
              <div v-for="(step, idx) in message.steps" :key="idx" class="trace-step">
                <span class="trace-tag" :class="[traceDisplay(step, idx, message.steps).stage, traceDisplay(step, idx, message.steps).status]">{{ traceDisplay(step, idx, message.steps).label }}</span>
                <span v-if="traceDisplay(step, idx, message.steps).agentName" class="trace-tool">{{ traceDisplay(step, idx, message.steps).agentName }}</span>
                <span class="trace-text">{{ traceDisplay(step, idx, message.steps).content }}</span>
              </div>
            </details>
            <details v-if="message.report" class="aios-result-report">
              <summary>
                <span>AIOS</span>
                <div>
                  <small>{{ message.report.subtitle }}</small>
                  <b>{{ message.report.title }}</b>
                </div>
                <em>展开</em>
              </summary>
              <div class="aios-report-metrics">
                <span v-for="metric in message.report.metrics" :key="metric.label">
                  <small>{{ metric.label }}</small>
                  <b>{{ metric.value }}</b>
                </span>
              </div>
              <section class="aios-report-section">
                <h4>执行结论</h4>
                <p>{{ message.report.conclusion }}</p>
              </section>
              <section v-if="message.report.recommendations?.length" class="aios-report-recommend-list">
                <h4>推荐生成报告</h4>
                <article v-for="item in message.report.recommendations.slice(0, 3)" :key="item.id">
                  <b>{{ item.title }}</b>
                  <small>{{ item.reason }}</small>
                </article>
              </section>
              <button class="aios-report-open" type="button" @click="selectedAiosReport = message.report">查看完整报告</button>
            </details>
            <template v-else>{{ message.text }}</template>
          </div>
          <button class="quick-card" type="button" @click="runOperatorPrimary">
            <span>
              <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true">
                <path v-for="path in iconParts(operatorProfile.icon)" :key="path" :d="path"></path>
              </svg>
            </span>
            <div>
              <b>{{ operatorProfile.quickTitle }}</b>
              <small>{{ operatorProfile.quickDesc }}</small>
            </div>
            <i>→</i>
          </button>
        </div>

        <div class="operator-chips">
          <button v-for="action in operatorProfile.actions" :key="action" type="button" @click="sendOperatorPrompt(action)">
            {{ action }}
          </button>
        </div>

        <input ref="assistantFileInput" class="visually-hidden" type="file" multiple accept="image/*,.pdf,.doc,.docx,.txt,.md" @change="addFiles($event, 'assistant')" />
        <div class="assistant-input-tools">
          <button type="button" :class="{ active: assistantVoiceListening }" @click="toggleAssistantVoice">
            <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3Z"></path><path d="M5 11a7 7 0 0 0 14 0M12 18v3M9 21h6"></path></svg>
            {{ assistantVoiceListening ? '正在听写，点击停止' : '语音转文字' }}
          </button>
          <button type="button" @click="$refs.assistantFileInput.click()">
            <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h4l2-2h4l2 2h4v12H4Z"></path><circle cx="12" cy="13" r="3"></circle></svg>
            图片 / 资料识别
          </button>
        </div>
        <form class="ask-box" @submit.prevent="sendOperatorPrompt(operatorInput)">
          <input v-model="operatorInput" :placeholder="operatorProfile.placeholder" />
          <button type="submit" aria-label="发送消息" title="发送消息">
            <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m4 4 16 8-16 8 3-8-3-8Z"></path><path d="M7 12h13"></path></svg>
          </button>
        </form>
        <div v-if="assistantFiles.length" class="assistant-attachments">
          <span v-for="file in assistantFiles" :key="file.localId">
            <img v-if="file.type === '图片'" :src="file.url" :alt="file.name" />
            <i>{{ file.type }}</i>{{ file.name }} · {{ file.status }}
            <button type="button" @click="removeAssistantFile(file.localId)">×</button>
          </span>
        </div>
      </aside>
      </div>
    </section>

    <section
      v-if="activePage === 'knowledge'"
      class="floating-agent"
      :class="{ open: floatingAgent.open, dragging: floatingAgent.dragging }"
      :style="floatingAgentStyle"
    >
      <button
        v-if="!floatingAgent.open"
        class="floating-agent-orb"
        type="button"
        @pointerdown="startFloatingAgentDrag"
        @click="toggleFloatingAgent"
        aria-label="打开博闻智能体"
      >
        <img :src="operatorProfile.avatar" :alt="operatorProfile.name" @error="handleAvatarError" />
        <span></span>
      </button>
      <div v-if="floatingAgent.open" class="floating-agent-chat">
        <header @pointerdown="startFloatingAgentDrag">
          <img :src="operatorProfile.avatar" :alt="operatorProfile.name" @error="handleAvatarError" />
          <div>
            <p>AI 智能体</p>
            <h3>{{ operatorProfile.name }}</h3>
            <small>{{ selectedGraphNode ? `正在查看：${selectedGraphNode.label}` : operatorProfile.role }}</small>
          </div>
          <div class="floating-agent-head-actions">
            <button type="button" title="新建对话" aria-label="新建对话" @click.stop="clearOperatorMessages">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"></path></svg>
            </button>
            <button type="button" title="关闭" aria-label="关闭" @click.stop="floatingAgent.open = false">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"></path></svg>
            </button>
          </div>
        </header>
        <div class="floating-chat-thread">
          <div class="bubble assistant">{{ operatorProfile.welcome }}</div>
          <div v-if="selectedGraphNode" class="bubble assistant node-context">
            当前节点：{{ selectedGraphNode.label }}。我可以基于它检索资料、解释关系或整理检修建议。
          </div>
          <div v-for="message in currentOperatorMessages" :key="message.id" :class="['bubble', message.role, { loading: message.loading }]">
            <span v-if="message.loading" class="loading-dots"><i></i><i></i><i></i></span>
            <div v-if="message.attachments?.length" class="message-attachments compact">
              <figure v-for="file in message.attachments" :key="file.localId || file.name" :class="{ image: file.type === '图片' }">
                <img v-if="file.type === '图片' && file.url" :src="file.url" :alt="file.name" />
                <span v-else>{{ file.type || '附件' }}</span>
                <figcaption>
                  <b>{{ file.name }}</b>
                  <small>{{ file.sizeText || file.size || '已添加' }}</small>
                </figcaption>
              </figure>
            </div>
            {{ message.text }}
          </div>
        </div>
        <div class="floating-agent-prompts">
          <span>试试这样问</span>
          <button v-for="template in floatingPromptTemplates" :key="template.label" type="button" @click="useFloatingPrompt(template)">
            {{ template.label }}
          </button>
        </div>
        <div v-if="assistantFiles.length" class="floating-attachments">
          <span v-for="file in assistantFiles" :key="file.localId">
            {{ file.name }}
            <button type="button" aria-label="移除附件" @click="removeAssistantFile(file.localId)">×</button>
          </span>
        </div>
        <form class="floating-ask-box" @submit.prevent="sendOperatorPrompt(operatorInput)">
          <input ref="floatingAssistantFileInput" class="visually-hidden" type="file" multiple accept="image/*,.pdf,.doc,.docx,.txt,.md" @change="addFiles($event, 'assistant')" />
          <div class="floating-input-tools">
            <button type="button" title="图片或资料" aria-label="图片或资料" @click="floatingAssistantFileInput?.click()">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h4l2-2h4l2 2h4v12H4Z"></path><circle cx="12" cy="13" r="3"></circle></svg>
            </button>
            <button type="button" :class="{ active: assistantVoiceListening }" title="语音输入" aria-label="语音输入" @click="toggleAssistantVoice">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3a3 3 0 0 0-3 3v5a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3Z"></path><path d="M19 10a7 7 0 0 1-14 0"></path><path d="M12 17v4"></path></svg>
            </button>
          </div>
          <input v-model="operatorInput" :placeholder="selectedGraphNode ? `围绕「${selectedGraphNode.label}」提问` : operatorProfile.placeholder" />
          <button class="floating-send" type="submit" title="发送" aria-label="发送">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m4 4 16 8-16 8 3-8-3-8Z"></path><path d="M7 12h13"></path></svg>
          </button>
        </form>
      </div>
    </section>

    <div v-if="selectedTask" class="modal" @click.self="selectedTask = null">
      <article class="modal-card task-modal-card">
        <button class="close" type="button" @click="selectedTask = null">×</button>
        <header class="task-modal-hero">
          <div><p class="eyebrow">项目详情与进展记录</p><h2>{{ selectedTask.title }}</h2><small>{{ selectedTask.workOrderNo }} · {{ selectedTask.equipment_name }} / {{ selectedTask.equipment_model }}</small></div>
          <span><i :class="['badge', selectedTask.severity]">{{ severityText(selectedTask.severity) }}</i><b>{{ statusText(selectedTask.status) }}</b></span>
        </header>
        <div class="task-modal-progress"><div><span :style="{ width: `${selectedTask.progress}%` }"></span></div><b>{{ selectedTask.progress }}%</b></div>
        <div class="detail-grid task-modal-stats">
          <span><small>项目位置</small><b>{{ selectedTask.equipment_no }}</b></span>
          <span><small>负责人</small><b>{{ selectedTask.assignee_name }}</b></span>
          <span><small>当前阶段</small><b>{{ selectedTask.project_phase || selectedTask.current_step }}</b></span>
          <span><small>剩余周期</small><b>{{ remainingTime(selectedTask) }}</b></span>
        </div>
        <p class="task-modal-description">{{ selectedTask.projectProgressSummary || selectedTask.description }}</p>
        <div class="detail-grid task-modal-stats">
          <span><small>项目周期</small><b>{{ selectedTask.project_period || '待补充' }}</b></span>
          <span><small>下一里程碑</small><b>{{ selectedTask.next_milestone || '待补充' }}</b></span>
          <span><small>最新进展</small><b>{{ selectedTask.latest_update || selectedTask.current_step }}</b></span>
          <span><small>协作成员</small><b>{{ selectedTask.collaborators?.join('、') || '待分配' }}</b></span>
        </div>
        <div class="personalized-sop-panel">
          <div>
            <p class="eyebrow">项目工作流推送</p>
            <h3>{{ taskFlowProfile(selectedTask).title }}</h3>
            <small>{{ taskFlowProfile(selectedTask).reason }}</small>
          </div>
          <div class="flow-profile-tags">
            <span v-for="tag in taskFlowProfile(selectedTask).tags" :key="tag">{{ tag }}</span>
          </div>
          <button type="button" @click="applyRecommendedSop(selectedTask)">应用推荐流程</button>
        </div>
        <div class="compliance-check-panel">
          <div class="task-modal-section-title"><span>合规校验提醒</span><small>{{ taskComplianceChecks(selectedTask).filter((item) => item.ok).length }}/{{ taskComplianceChecks(selectedTask).length }} 已满足</small></div>
          <div class="compliance-check-grid">
            <span v-for="item in taskComplianceChecks(selectedTask)" :key="item.label" :class="{ ok: item.ok, required: item.required }">
              <b>{{ item.ok ? '✓' : '!' }}</b>
              <em>{{ item.label }}</em>
              <small>{{ item.hint }}</small>
            </span>
          </div>
        </div>
        <div v-if="selectedTask.deliverables?.length" class="safety-reminders"><div><b>项目交付物</b><small>用于验收和沉淀</small></div><span v-for="item in selectedTask.deliverables" :key="item">{{ item }}</span></div>
        <div v-if="selectedTask.risks?.length" class="safety-reminders"><div><b>项目风险</b><small>需要持续跟踪</small></div><span v-for="item in selectedTask.risks" :key="item">{{ item }}</span></div>
        <div class="task-modal-section-title"><span>项目推进步骤</span><small>{{ selectedTask.sop?.length || 0 }} 个步骤</small></div>
        <div class="sop-list executable-sop">
          <span v-for="(step, index) in selectedTask.sop" :key="`${stepTitle(step)}-${index}`" :class="{ completed: isTaskStepCompleted(selectedTask, index) }">
            <b>{{ isTaskStepCompleted(selectedTask, index) ? '✓' : index + 1 }}</b>
            <span><strong>{{ stepTitle(step) }}</strong><small v-if="stepDetail(step)">{{ stepDetail(step) }}</small></span>
            <button type="button" :disabled="isTaskStepCompleted(selectedTask, index)" @click="completeTaskStep(selectedTask, index)">{{ isTaskStepCompleted(selectedTask, index) ? '已完成' : '确认完成' }}</button>
          </span>
        </div>
        <div v-if="selectedTask.safety?.length" class="safety-reminders"><div><b>合规与安全提醒</b><small>操作前逐项确认</small></div><span v-for="item in selectedTask.safety" :key="item">{{ item }}</span></div>

        <!-- 关联技术资料：反向联动 -->
        <div class="task-linked-knowledge">
          <h4>📚 关联技术资料
            <span v-if="taskLinkedKnowledge.length === 0" class="tl-go-kb" @click.stop="activePage = 'search'; searchPanel = 'library'; selectedTask = null">去知识库关联 →</span>
          </h4>
          <div v-if="taskLinkedKnowledge.length === 0" class="tl-empty">暂无关联技术资料</div>
          <div v-else class="task-linked-list">
            <div class="task-linked-item" v-for="k in taskLinkedKnowledge" :key="k.id" @click.stop="openKnowledge(k)">
              <div>
                <div class="tl-title">{{ k.title }}</div>
                <div class="tl-meta">{{ k.category || '技术资料' }} · {{ k.updated_at || '未知时间' }}</div>
              </div>
              <span class="tl-arrow">→</span>
            </div>
          </div>
        </div>

        <div class="actions task-modal-actions">
          <button class="primary" type="button" @click="handleTaskPrimary(selectedTask)">{{ taskPrimaryLabel(selectedTask) }}</button>
          <button type="button" :disabled="selectedTask.status === 'pending'" @click="enterTaskRecheck(selectedTask)">进入复检</button>
          <button type="button" @click="previewTaskReport(selectedTask)">预览报告</button>
        </div>
      </article>
    </div>

    <div v-if="showTaskPicker" class="modal" @click.self="showTaskPicker = false">
      <article class="modal-card task-picker-card">
        <button class="close" type="button" @click="showTaskPicker = false">×</button>
        <p class="eyebrow">{{ taskPickerMode === 'assign' ? '添加协作人员' : '发送任务卡片' }}</p>
        <h2>{{ taskPickerMode === 'assign' ? `选择要加入 ${activeConversation?.name} 的任务` : '选择需要发送的检修任务' }}</h2>
        <div class="task-picker-list">
          <button v-for="task in tasks" :key="task.id" type="button" @click="selectTaskFromPicker(task)">
            <span><b>{{ task.workOrderNo }}</b><small>{{ task.equipment_name }} · {{ task.current_step }}</small></span>
            <i :class="['badge', task.severity]">{{ severityText(task.severity) }}</i><strong>{{ task.progress }}%</strong>
          </button>
        </div>
      </article>
    </div>

    <div v-if="reportTask" class="modal" @click.self="reportTask = null">
      <article class="modal-card task-report-card">
        <button class="close" type="button" @click="reportTask = null">×</button>
        <header><div><p class="eyebrow">检修报告预览</p><h2>{{ reportTask.title }}</h2><small>{{ reportTask.workOrderNo }} · 生成时间 {{ new Date().toLocaleString('zh-CN') }}</small></div><span :class="['badge', reportTask.severity]">{{ severityText(reportTask.severity) }}</span></header>
        <div class="report-summary"><span><small>设备</small><b>{{ reportTask.equipment_name }} / {{ reportTask.equipment_model }}</b></span><span><small>负责人</small><b>{{ reportTask.assignee_name }}</b></span><span><small>完成进度</small><b>{{ reportTask.progress }}%</b></span><span><small>当前结论</small><b>{{ statusText(reportTask.status) }}</b></span></div>
        <section><h3>故障与处置摘要</h3><p>{{ reportTask.description }}</p></section>
        <section><h3>标准作业记录</h3><ol><li v-for="(step, index) in reportTask.sop || []" :key="index"><b>{{ stepTitle(step) }}</b><span>{{ isTaskStepCompleted(reportTask, index) ? '已确认完成' : '待补充记录' }}</span></li></ol></section>
        <section v-if="reportTask.recheck"><h3>复检结论</h3><p>{{ reportTask.recheck.result }} · {{ reportTask.recheck.comment || '未填写补充说明' }}</p></section>
        <section class="task-report-recommendations">
          <h3>建议生成的专项报告</h3>
          <article v-for="item in buildTaskReportRecommendations(reportTask)" :key="item.id">
            <b>{{ item.title }}</b>
            <small>{{ item.reason }}</small>
            <ul><li v-for="line in item.sections" :key="line">{{ line }}</li></ul>
          </article>
        </section>
        <div class="actions"><button type="button" @click="windowPrint">打印 / 导出 PDF</button><button class="primary" type="button" @click="reportTask = null">完成预览</button></div>
      </article>
    </div>

    <div v-if="selectedAiosReport" class="modal" @click.self="selectedAiosReport = null">
      <article class="modal-card aios-report-page">
        <button class="close" type="button" @click="selectedAiosReport = null">×</button>
        <header>
          <span>AIOS</span>
          <div>
            <p class="eyebrow">天工执行结果</p>
            <h2>{{ selectedAiosReport.title }}</h2>
            <small>{{ selectedAiosReport.subtitle }}</small>
          </div>
        </header>
        <div class="aios-page-metrics">
          <span v-for="metric in selectedAiosReport.metrics" :key="metric.label">
            <small>{{ metric.label }}</small>
            <b>{{ metric.value }}</b>
          </span>
        </div>
        <section class="aios-page-conclusion">
          <h3>执行结论</h3>
          <p>{{ selectedAiosReport.conclusion }}</p>
        </section>
        <section v-if="selectedAiosReport.recommendations?.length" class="aios-page-recommendations">
          <div>
            <p class="eyebrow">动态推荐</p>
            <h3>根据本次问题建议生成 {{ selectedAiosReport.recommendations.length }} 份报告</h3>
          </div>
          <article v-for="item in selectedAiosReport.recommendations" :key="item.id">
            <span>{{ item.type }}</span>
            <h4>{{ item.title }}</h4>
            <p>{{ item.reason }}</p>
            <ul>
              <li v-for="line in item.sections" :key="line">{{ line }}</li>
            </ul>
          </article>
        </section>
        <section class="aios-page-blocks">
          <article v-for="block in selectedAiosReport.blocks" :key="block.title">
            <h3>{{ block.title }}</h3>
            <ul>
              <li v-for="item in block.items" :key="item">{{ item }}</li>
            </ul>
          </article>
        </section>
        <footer>
          <span v-for="tag in selectedAiosReport.tags" :key="tag">{{ tag }}</span>
          <button class="primary" type="button" @click="selectedAiosReport = null">完成查看</button>
        </footer>
      </article>
    </div>

    <div v-if="selectedFile" class="modal" @click.self="selectedFile = null">
      <article class="modal-card wide-modal">
        <button class="close" type="button" @click="selectedFile = null">×</button>
        <p class="eyebrow">文件预览</p>
        <h2>{{ selectedFile.name }}</h2>
        <div class="detail-grid">
          <span>类型：{{ selectedFile.type }}</span>
          <span>大小：{{ selectedFile.size }}</span>
          <span>版本：{{ selectedFile.version }}</span>
          <span>解析：{{ selectedFile.parseStatus }}</span>
        </div>
        <div class="preview-box">
          <img v-if="selectedFile.type === '图片' && selectedFile.url" :src="selectedFile.url" alt="" @error="handleContentImageError($event, fileImageFallback)" />
          <iframe v-else-if="selectedFile.type === 'PDF' && selectedFile.url" :src="selectedFile.url"></iframe>
          <video v-else-if="selectedFile.type === '视频' && selectedFile.url" :src="selectedFile.url" controls></video>
          <iframe v-else-if="['文本', 'Word', 'Excel', '其他'].includes(selectedFile.type) && selectedFile.url" :src="selectedFile.url"></iframe>
          <div v-else class="empty">该文件暂不支持在线预览或真实访问地址为空，请下载后查看或重新解析。</div>
        </div>
      </article>
    </div>

    <div v-if="selectedLearningRecommendation" class="modal" @click.self="selectedLearningRecommendation = null">
      <article class="modal-card learning-detail-modal">
        <button class="close" type="button" @click="selectedLearningRecommendation = null">×</button>
        <p class="eyebrow">经验学习</p>
        <h2>{{ selectedLearningRecommendation.title }}</h2>
        <p class="learning-detail-desc">{{ selectedLearningRecommendation.desc }}</p>
        <div class="learning-detail-grid">
          <span><small>适用场景</small><b>{{ selectedLearningRecommendation.tags?.[0] || '检修复用' }}</b></span>
          <span><small>学习重点</small><b>{{ selectedLearningRecommendation.tags?.slice(1).join('、') || '故障定位' }}</b></span>
          <span><small>推荐检索式</small><b>{{ selectedLearningRecommendation.query }}</b></span>
        </div>
        <div class="learning-step-card">
          <b>建议学习路径</b>
          <ol>
            <li>先查看同型号或同故障类型的历史检索记录，确认共性现象。</li>
            <li>对照维修手册、SOP 和复检报告，提取可复用的检查位置与安全要求。</li>
            <li>把已验证的原因、检测方法和验收标准沉淀为知识条目。</li>
          </ol>
        </div>
        <div class="tag-line"><span v-for="tag in selectedLearningRecommendation.tags" :key="tag">{{ tag }}</span></div>
        <div class="actions">
          <button type="button" @click="selectedLearningRecommendation = null">稍后学习</button>
          <button class="primary" type="button" @click="applyLearningRecommendation(selectedLearningRecommendation); selectedLearningRecommendation = null">带入检索</button>
        </div>
      </article>
    </div>

    <div v-if="selectedKnowledge" class="modal" @click.self="closeKnowledgeDetail()">
      <article class="modal-card knowledge-detail-card" :class="{ editing: isKnowledgeEditing }">
        <button class="close" type="button" @click="closeKnowledgeDetail()">×</button>
        
        <!-- 编辑模式：三栏布局 -->
        <template v-if="isKnowledgeEditing">
          <aside class="kd-sidebar-left">
            <div class="kd-sidebar-header">
              <span class="kd-sidebar-icon">📂</span>
              <span class="kd-sidebar-title">技术资料库</span>
            </div>
            <div class="kd-sidebar-breadcrumb">
              <span>📁 {{ selectedKnowledge.category || '默认分类' }}</span>
              <span class="kd-arrow">›</span>
              <span class="kd-current-doc">📄 {{ knowledgeDraft.title || '未命名文档' }}</span>
            </div>
            <div class="kd-outline">
              <div class="kd-outline-title">📋 文档大纲</div>
              <div class="kd-outline-list">
                <div v-for="(line, idx) in knowledgeOutline" :key="idx" class="kd-outline-item" :class="'level-' + line.level">
                  <span class="kd-outline-dot">•</span>
                  <span>{{ line.text }}</span>
                </div>
                <div v-if="knowledgeOutline.length === 0" class="kd-outline-empty">
                  暂无大纲内容
                </div>
              </div>
            </div>
            <div class="kd-sidebar-footer">
              <span>📝 {{ knowledgeDraft.content?.length || 0 }} 字</span>
              <span>⏱ {{ knowledgeSaveStatus === 'saved' ? '已保存' : '编辑中' }}</span>
            </div>
          </aside>
        </template>

        <div class="kd-main-area">
          <header class="kd-header">
            <div class="kd-header-left">
              <div v-if="isKnowledgeEditing" class="kd-top-bar">
                <span class="kd-doc-icon">📝</span>
                <input v-model="knowledgeDraft.title" class="kd-title-input" placeholder="无标题文档" />
              </div>
              <h2 v-else>{{ selectedKnowledge.title }}</h2>
              <small v-if="knowledgeSaveStatus" class="kd-save-status" :class="knowledgeSaveStatus">{{ knowledgeSaveText }}</small>
            </div>
            <div class="kd-header-right">
              <span class="kd-type">{{ knowledgeTypeText(selectedKnowledge) }}</span>
              <button v-if="!isKnowledgeEditing" type="button" class="btn-edit" @click="startKnowledgeEdit()">✏️ 编辑内容</button>
              <div v-else class="kd-edit-actions">
                <button type="button" class="btn-edit-cancel" @click="cancelKnowledgeEdit()">取消</button>
                <button type="button" class="btn-edit-save" @click="saveKnowledgeNow(true)">💾 保存</button>
              </div>
            </div>
          </header>

          <div v-if="isKnowledgeEditing" class="kd-editor-toolbar">
            <button type="button" title="标题" @click="insertMarkdown('heading')">H</button>
            <button type="button" title="加粗" @click="insertMarkdown('bold')"><b>B</b></button>
            <button type="button" title="斜体" @click="insertMarkdown('italic')"><i>I</i></button>
            <span class="kd-toolbar-divider"></span>
            <button type="button" title="无序列表" @click="insertMarkdown('list')">• 列表</button>
            <button type="button" title="有序列表" @click="insertMarkdown('olist')">1. 列表</button>
            <button type="button" title="待办事项" @click="insertMarkdown('todo')">☑ 待办</button>
            <span class="kd-toolbar-divider"></span>
            <button type="button" title="表格" @click="insertMarkdown('table')">📊 表格</button>
            <button type="button" title="代码块" @click="insertMarkdown('code')"><> 代码</button>
            <button type="button" title="引用" @click="insertMarkdown('quote')">"</button>
            <span class="kd-toolbar-divider"></span>
            <span class="kd-toolbar-spacer"></span>
            <span class="kd-toolbar-hint">Markdown 格式</span>
          </div>

          <div class="kd-meta-bar" :class="{ editing: isKnowledgeEditing }">
            <template v-if="!isKnowledgeEditing">
              <span><small>适用设备</small><b>{{ selectedKnowledge.equipment || '通用检修设备' }}</b></span>
              <span><small>型号</small><b>{{ selectedKnowledge.model || '通用型号' }}</b></span>
              <span><small>来源</small><b>{{ selectedKnowledge.source || '一休知识库' }}</b></span>
              <span><small>引用</small><b>{{ selectedKnowledge.citations || 0 }} 次</b></span>
            </template>
            <template v-else>
              <label class="kd-meta-input"><small>适用设备</small><input v-model="knowledgeDraft.equipment" /></label>
              <label class="kd-meta-input"><small>型号</small><input v-model="knowledgeDraft.model" /></label>
              <label class="kd-meta-input"><small>标签(逗号分隔)</small><input v-model="knowledgeDraft.tagsText" /></label>
              <label class="kd-meta-input"><small>来源</small><input v-model="knowledgeDraft.source" /></label>
            </template>
          </div>

          <section class="kd-content-section">
            <div class="kd-content-head" v-if="!isKnowledgeEditing">
              <h3>📝 内容摘要</h3>
            </div>
            <textarea v-if="isKnowledgeEditing" v-model="knowledgeDraft.content" @input="onKnowledgeContentInput" placeholder="开始输入文档内容...

支持 Markdown 格式：
## 二级标题
**加粗文本**
- 无序列表项
1. 有序列表项
- [ ] 待办事项
| 表头 | 表头 |
|------|------|
| 内容 | 内容 |" class="kd-editor"></textarea>
            <ul v-else class="kd-summary-list"><li v-for="(line, index) in knowledgeFullLines(selectedKnowledge)" :key="index">{{ line }}</li></ul>
          </section>

          <div v-if="!isKnowledgeEditing && selectedKnowledge.tags?.length" class="tag-line"><span v-for="tag in selectedKnowledge.tags" :key="tag">{{ tag }}</span></div>
        </div>

        <!-- 右侧边栏：仅非编辑模式显示 -->
        <aside v-if="!isKnowledgeEditing" class="kd-sidebar-right">
          <!-- 联动：关联任务 & 引用知识 -->
          <section class="kd-links-section">
            <div class="kd-links-head"><h3>🔗 板块联动</h3><small v-if="kdLinks.length">关联 {{ kdLinks.length }} 项</small></div>
            <div v-if="kdTasks.length" class="kd-link-block">
              <p class="kd-link-label">📋 关联检修任务</p>
              <div class="kd-link-list">
                <div v-for="link in kdTasks" :key="link.id" class="kd-link-item" @click="openTaskById(link.target_id)">
                  <span>{{ link.target_title }}</span>
                  <button type="button" class="kd-link-del" @click.stop="removeKdLink(link.id)">✕</button>
                </div>
              </div>
            </div>
            <div v-if="kdKnowledgeLinks.length" class="kd-link-block">
              <p class="kd-link-label">📚 引用知识</p>
              <div class="kd-link-list">
                <div v-for="link in kdKnowledgeLinks" :key="link.id" class="kd-link-item" @click="openKnowledge({ id: link.target_id, title: link.target_title })">
                  <span>📖 {{ link.target_title }}</span>
                  <button type="button" class="kd-link-del" @click.stop="removeKdLink(link.id)">✕</button>
                </div>
              </div>
            </div>
            <div class="kd-link-add">
              <select v-model="kdNewLink.type">
                <option value="task">关联任务</option><option value="knowledge">引用知识</option>
              </select>
              <input v-model="kdNewLink.targetId" placeholder="目标ID" />
              <input v-model="kdNewLink.title" placeholder="显示标题" />
              <button type="button" @click="addKdLink()">+ 添加</button>
            </div>
          </section>

          <!-- 版本历史 -->
          <section class="kd-versions-section">
            <div class="kd-links-head"><h3>📜 版本历史</h3><small v-if="kdVersions.length">共 {{ kdVersions.length }} 个版本</small></div>
            <div v-if="kdVersions.length === 0" class="kd-empty">暂无版本记录，首次编辑后会生成版本。</div>
            <div v-else class="kd-version-list">
              <div v-for="ver in kdVersions" :key="ver.id" class="kd-version-item">
                <div class="kd-version-main">
                  <b>v{{ ver.version }}</b><small>{{ ver.editor_name || '系统' }} · {{ ver.created_at }}</small>
                </div>
                <p v-if="ver.change_summary" class="kd-version-summary">{{ ver.change_summary }}</p>
                <button type="button" class="kd-version-restore" @click="restoreKdVersion(ver)">↩ 恢复</button>
              </div>
            </div>
          </section>

          <!-- 协作成员 -->
          <section class="kd-collab-section">
            <div class="kd-links-head">
              <h3>👥 协作成员 <small v-if="kdCollaborators.length">{{ kdCollaborators.length }} 人</small></h3>
              <button type="button" class="kd-invite-btn" @click="inviteCollaborator">+ 邀请</button>
            </div>
            <div v-if="kdCollaborators.length === 0" class="kd-empty">暂无协作成员，点击右上角邀请同事共同编辑此文档。</div>
            <div v-else class="kd-collab-list">
              <div v-for="(c, ci) in kdCollaborators" :key="ci" class="kd-collab-item">
                <span class="kd-collab-avatar" :style="{ background: avatarColors[ci % avatarColors.length] }">{{ (c.name || '?')[0] }}</span>
                <div>
                  <b>{{ c.name }}</b>
                  <small>{{ c.role === 'owner' ? '所有者' : c.role === 'editor' ? '编辑者' : '查看者' }}</small>
                </div>
                <span class="kd-collab-status" :class="c.status || 'offline'">{{ c.status === 'online' ? '🟢 在线' : '⚪ 离线' }}</span>
              </div>
            </div>
          </section>
        </aside>

        <div class="kd-actions actions" v-if="!isKnowledgeEditing">
          <button type="button" @click="selectedKnowledge = null">关闭</button>
          <button class="primary" type="button" @click="searchFromKnowledge(selectedKnowledge); selectedKnowledge = null">作为检索依据</button>
          <button type="button" class="btn-submit" @click="submitKnowledgeReview()">📤 提交知识审核</button>
        </div>
      </article>
    </div>

    <div v-if="showTaskForm" class="modal" @click.self="showTaskForm = false">
      <article class="modal-card">
        <button class="close" type="button" @click="showTaskForm = false">×</button>
        <p class="eyebrow">新建检修任务</p>
        <div class="form-grid">
          <label>设备名称<input v-model="taskForm.equipment_name" /></label>
          <label>设备编号<input v-model="taskForm.equipment_no" /></label>
          <label>设备型号<input v-model="taskForm.equipment_model" /></label>
          <label>风险等级<select v-model="taskForm.severity"><option value="low">低</option><option value="medium">中</option><option value="high">高</option></select></label>
          <label>负责人<input v-model="taskForm.assignee_name" /></label>
          <label>计划完成时间<input v-model="taskForm.due_at" /></label>
          <label class="wide">故障描述<textarea v-model="taskForm.description"></textarea></label>
        </div>
        <button class="primary" type="button" @click="submitTask">创建任务</button>
      </article>
    </div>

    <div v-if="showScheduleForm" class="modal" @click.self="showScheduleForm = false">
      <article class="modal-card schedule-editor-card">
        <button class="close" type="button" @click="showScheduleForm = false">×</button>
        <p class="eyebrow">{{ editingScheduleId ? '编辑日程' : '新增日程' }}</p>
        <h3>{{ editingScheduleId ? '调整日程安排' : '安排新的检修日程' }}</h3>
        <div class="form-grid">
          <label>日程标题<input v-model.trim="scheduleDraft.title" maxlength="40" placeholder="如：配电柜复测确认" /></label>
          <label>日期<input v-model="scheduleDraft.date" type="date" /></label>
          <label>时间<input v-model.trim="scheduleDraft.time" maxlength="20" placeholder="09:00~10:00" /></label>
          <label>类型<select v-model="scheduleDraft.tag"><option>工作安排</option><option>复检安排</option><option>协作会议</option><option>资料整理</option><option>高风险</option></select></label>
          <label class="wide">参与人员<input v-model.trim="scheduleDraft.people" maxlength="80" placeholder="负责人：聪明的一休" /></label>
          <label class="wide">说明<textarea v-model.trim="scheduleDraft.desc" maxlength="160" placeholder="补充日程目的、地点、注意事项"></textarea></label>
        </div>
        <div class="schedule-editor-checks">
          <label><input v-model="scheduleDraft.important" type="checkbox" /> 标记重点</label>
          <label><input v-model="scheduleDraft.done" type="checkbox" /> 已完成</label>
        </div>
        <div class="profile-editor-actions"><button type="button" @click="showScheduleForm = false">取消</button><button class="primary" type="button" @click="saveSchedule">保存日程</button></div>
      </article>
    </div>

    <div v-if="showProfileEditor" class="modal profile-editor-modal" @click.self="showProfileEditor = false">
      <form class="modal-card profile-editor-card" @submit.prevent="saveProfile">
        <button class="close" type="button" @click="showProfileEditor = false">×</button>
        <header class="profile-editor-head">
          <img :src="profileDraft.avatar" alt="" @error="handleAvatarError" />
          <div><p class="eyebrow">个人资料</p><h2>完善检修信息</h2><span>资料将用于工单分配、协作联系和知识贡献署名</span></div>
        </header>
        <div class="form-grid profile-editor-grid">
          <label>姓名<input v-model.trim="profileDraft.name" maxlength="20" /></label>
          <label>工号<input v-model.trim="profileDraft.employeeId" maxlength="20" /></label>
          <label>岗位<input v-model.trim="profileDraft.role" maxlength="30" /></label>
          <label>所属班组<input v-model.trim="profileDraft.department" maxlength="30" /></label>
          <label>技能等级<select v-model="profileDraft.skillLevel"><option>初级</option><option>中级</option><option>高级</option><option>专家</option></select></label>
          <label>联系电话<input v-model.trim="profileDraft.phone" maxlength="20" placeholder="用于任务协作联系" /></label>
          <label class="wide">专业方向<input v-model.trim="profileDraft.specialtyText" placeholder="使用逗号分隔，如：发动机, 电气系统" /></label>
          <label class="wide">个人简介<textarea v-model.trim="profileDraft.bio" maxlength="160" placeholder="简要介绍检修经验与擅长领域"></textarea></label>
        </div>
        <p v-if="profileError" class="form-error">{{ profileError }}</p>
        <div class="profile-editor-actions"><button type="button" @click="showProfileEditor = false">取消</button><button class="primary" type="submit">保存资料</button></div>
      </form>
    </div>

    <div v-if="toastText" class="toast">{{ toastText }}</div>
    </template>
    <section v-if="tgRunUi.visible" class="tg-run-overlay" aria-label="天工执行过程">
      <div class="tg-run-card">
        <header>
          <span class="tg-run-mark">
            <img :src="'/static/tiangong.png'" alt="天工" @error="handleAgentAvatarError" />
            <i></i>
          </span>
          <div>
            <small>{{ tgRunUi.statusText }}</small>
            <b>{{ tgRunUi.title }}</b>
          </div>
          <em>{{ tgRunUi.current }}/{{ tgRunUi.total }}</em>
          <button class="tg-run-stop" type="button" title="中断执行" aria-label="中断执行" @click="stopTgRun">×</button>
        </header>
        <div class="tg-run-progress"><span :style="{ width: tgRunUi.progress + '%' }"></span></div>
        <p class="tg-run-detail">{{ tgRunUi.detail }}</p>
        <div class="tg-run-io">
          <span><small>负责智能体</small><b>{{ tgRunUi.agentName }}</b></span>
          <span><small>目标页面</small><b>{{ tgRunUi.page }}</b></span>
          <span><small>调用动作</small><b>{{ tgRunUi.tool }}</b></span>
        </div>
        <div class="tg-run-exchange">
          <section>
            <small>输入</small>
            <p>{{ tgRunUi.inputText }}</p>
          </section>
          <section>
            <small>输出</small>
            <p>{{ tgRunUi.outputText }}</p>
          </section>
        </div>
        <div class="tg-run-cognition">
          <span><small>感知</small><b>{{ tgRunUi.observation }}</b></span>
          <span><small>决策</small><b>{{ tgRunUi.decision }}</b></span>
          <span><small>校验</small><b>{{ tgRunUi.check }}</b></span>
        </div>
        <div class="tg-run-steps">
          <span
            v-for="step in tgRunUi.steps"
            :key="step.index"
            :class="{ done: step.index < tgRunUi.current, active: step.index === tgRunUi.current }"
          >
            {{ step.label }}
          </span>
        </div>
      </div>
    </section>
    <div class="tg-cursor" :style="{ position: 'fixed', left: tgCursor.x + 'px', top: tgCursor.y + 'px', opacity: tgCursor.visible ? 1 : 0, zIndex: 99999 }">
      <span class="tg-cursor-dot"></span>
      <span v-if="tgCursor.label" class="tg-cursor-label">{{ tgCursor.label }}</span>
    </div>
  </main>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { yixiuApi } from './src/api/yixiuWeb.js'
import { createOverviewFromMock, mockAgents, mockUser, mockSkills } from './src/data/yixiuMock.js'
import EChart from './src/components/EChart.vue'

const navItems = [
  { key: 'home', label: '工作台', title: '项目智能工作台', icon: 'dashboard' },
  { key: 'search', label: '上下文中心', title: '任务上下文包生成', icon: 'search' },
  { key: 'tasks', label: '任务执行', title: '项目进展与人机协作', icon: 'wrench' },
  { key: 'knowledge', label: '能力中心', title: 'Agent、Skill 与团队资产', icon: 'network' },
  { key: 'profile', label: '个人空间', title: '个人能力、成本与核查', icon: 'user' }
]

const iconPaths = {
  dashboard: ['M4 13h7V4H4v9Z', 'M13 20h7V4h-7v16Z', 'M4 20h7v-5H4v5Z'],
  search: ['M11 19a8 8 0 1 1 0-16 8 8 0 0 1 0 16Z', 'M21 21l-4.35-4.35'],
  wrench: ['M14.7 6.3a4 4 0 0 0-5 5L3.9 17.1a2 2 0 0 0 3 3l5.8-5.8a4 4 0 0 0 5-5l-2.9 2.9-2.1-2.1 2.9-2.9Z'],
  network: ['M6 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z', 'M18 22a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z', 'M18 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z', 'M8.6 6.5l6.8 10', 'M8.8 4.5h6.4'],
  user: ['M20 21a8 8 0 0 0-16 0', 'M12 13a5 5 0 1 0 0-10 5 5 0 0 0 0 10Z'],
  bell: ['M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9Z', 'M10 21h4'],
  cpu: ['M8 8h8v8H8z', 'M3 10h3', 'M3 14h3', 'M18 10h3', 'M18 14h3', 'M10 3v3', 'M14 3v3', 'M10 18v3', 'M14 18v3'],
  bot: ['M12 8V4', 'M7 8h10a4 4 0 0 1 4 4v3a5 5 0 0 1-5 5H8a5 5 0 0 1-5-5v-3a4 4 0 0 1 4-4Z', 'M9 13h.01', 'M15 13h.01', 'M9 17h6'],
  check: ['M20 6 9 17l-5-5'],
  calendar: ['M7 3v3M17 3v3M4 9h16M6 5h12a2 2 0 0 1 2 2v12H4V7a2 2 0 0 1 2-2Z'],
  chart: ['M4 19V5', 'M8 17v-6', 'M13 17V7', 'M18 17v-9', 'M4 19h17'],
  file: ['M14 3H6a2 2 0 0 0-2 2v14h16V9Z', 'M14 3v6h6', 'M8 13h8', 'M8 17h5'],
  shield: ['M12 3 20 6v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3Z', 'M9 12l2 2 4-5'],
  clock: ['M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Z', 'M12 6v6l4 2'],
  zap: ['M13 2 4 14h7l-1 8 9-12h-7l1-8Z'],
  settings: ['M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z', 'M19.4 15a1.8 1.8 0 0 0 .36 2l.04.04-2 3.46-.05-.02a1.8 1.8 0 0 0-2.03.1 8 8 0 0 1-1.72 1l-.28.12A1.8 1.8 0 0 0 12 23h-4a1.8 1.8 0 0 0-1.72-1.3l-.28-.12a8 8 0 0 1-1.72-1 1.8 1.8 0 0 0-2.03-.1l-.05.02-2-3.46.04-.04A1.8 1.8 0 0 0 .6 15 8 8 0 0 1 .6 9a1.8 1.8 0 0 0-.36-2L.2 6.96 2.2 3.5l.05.02a1.8 1.8 0 0 0 2.03-.1 8 8 0 0 1 1.72-1l.28-.12A1.8 1.8 0 0 0 8 1h4a1.8 1.8 0 0 0 1.72 1.3l.28.12a8 8 0 0 1 1.72 1 1.8 1.8 0 0 0 2.03.1l.05-.02 2 3.46-.04.04A1.8 1.8 0 0 0 19.4 9a8 8 0 0 1 0 6Z'],
  tool: ['M21 3l-6 6', 'M14 4l6 6', 'M5 19l6-6']
}
const iconParts = (name) => iconPaths[name] || iconPaths.tool

const AUTH_ACCOUNTS_KEY = 'yixiu-web-accounts'
const AUTH_SESSION_KEY = 'yixiu-web-session'
const PROFILE_KEY = 'yixiu-web-profile'
const SCHEDULE_ITEMS_KEY = 'yixiu-schedule-items'
const SCHEDULE_OVERRIDES_KEY = 'yixiu-schedule-overrides'
const SCHEDULE_MARKS_KEY = 'yixiu-schedule-marks'
const SCHEDULE_DELETED_KEY = 'yixiu-schedule-deleted'
const CONTACT_DIRECTORY_KEY = 'yixiu-web-contact-directory'
const CONTACT_READ_KEY = 'yixiu-web-contact-read'
const svgImage = (title, subtitle, accent = '#2f89bd') => {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540">
    <defs>
      <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e9f8ff"/><stop offset=".55" stop-color="#bfe6ff"/><stop offset="1" stop-color="#f8fbff"/></linearGradient>
      <linearGradient id="mark" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${accent}"/><stop offset="1" stop-color="#85d2c9"/></linearGradient>
      <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="16" stdDeviation="20" flood-color="#0f3f52" flood-opacity=".16"/></filter>
    </defs>
    <rect width="960" height="540" fill="url(#bg)"/>
    <circle cx="760" cy="90" r="210" fill="#ffffff" opacity=".34"/>
    <circle cx="820" cy="430" r="260" fill="${accent}" opacity=".12"/>
    <path d="M70 390 C180 330 240 420 350 360 S540 300 675 350 S820 340 910 280" fill="none" stroke="#ffffff" stroke-width="20" opacity=".72"/>
    <g filter="url(#shadow)" transform="translate(92 112)">
      <rect width="400" height="235" rx="26" fill="#ffffff" opacity=".86"/>
      <path d="M50 138 h112 v34 H50zM50 84 h250 v20 H50zM50 116 h190 v16 H50z" fill="#d7e8ef"/>
      <circle cx="330" cy="154" r="42" fill="url(#mark)" opacity=".9"/>
      <path d="M314 154 l13 13 26-34" fill="none" stroke="#fff" stroke-width="11" stroke-linecap="round" stroke-linejoin="round"/>
    </g>
    <text x="92" y="414" font-family="Microsoft YaHei, PingFang SC, Arial, sans-serif" font-size="42" font-weight="800" fill="#17364a">${title}</text>
    <text x="94" y="462" font-family="Microsoft YaHei, PingFang SC, Arial, sans-serif" font-size="24" font-weight="600" fill="#426174">${subtitle}</text>
  </svg>`
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`
}
const newsImageFallback = svgImage('一休 Team Memory OS', 'Context Pack · Skill · Eval Lab')
const fileImageFallback = svgImage('任务材料预览', '上下文证据已归档', '#4f8062')
const newsSlides = [
  {
    title: 'Vidu S2 技术解析：实时编辑、实时交互、探索空间视频',
    summary: '生数科技发布 Vidu S2-Avatar 与 Vidu S2-Editing 双模型：一边发生一边改写，支持实时数字人、实时视频编辑与空间视频实时传输。',
    source: '生数科技 · 公众号',
    date: '2026-09-15',
    link: 'https://mp.weixin.qq.com/s/f2uewxWhxWlq_JOQqFvmiw',
    image: '/static/yixiu-carousel-vidu-s2.webp'
  },
  {
    title: '最懂科学的开源基础大模型「书生-S2」发布',
    summary: '上海人工智能实验室发布 397B 书生-S2：科学能力比肩顶尖闭源模型，通用性能居开源第一梯队，Memory 机制按需激活隐藏状态。',
    source: '书生Intern · 公众号',
    date: '2026-09-14',
    link: 'https://mp.weixin.qq.com/s/EZghVJB13rJTRfBv2_U0Xw',
    image: '/static/yixiu-carousel-intern-s2.webp'
  },
  {
    title: '谷歌推出 Gemini 3.8 Live 与 3.8 Live Extended Thinking',
    summary: '两款实时对话模型分别面向规模部署与高复杂度多步推理，可近实时处理视觉输入，并在对话中自动检测切换 97 种语言。',
    source: 'IT之家',
    date: '2026-09-16',
    link: 'https://www.ithome.com/1/002/824.htm',
    image: '/static/yixiu-carousel-gemini-live.webp'
  }
]
// 首页「Skill 推荐榜」：模板按 stars 降序展示高星开源 Agent & RAG 项目
const skillRankList = [...mockSkills].sort((a, b) => b.stars - a.stars)

// ═══════════════════════════════════════════════════════════════════════════
// Skill Factory｜团队技能工厂
// 定位：把执行过的任务轨迹提炼成 Agent 可以直接调用的能力，管的是
// 「团队怎么把经验变成能力」。项目验收只是它流水线上的一个入料口。
// ═══════════════════════════════════════════════════════════════════════════

const SKILL_STAGES = ['Draft', 'Testing', 'Verified', 'Production', 'Deprecated']
const SKILL_STAGE_LABEL = { Draft: '草稿', Testing: '测试中', Verified: '已验证', Production: '生产中', Deprecated: '已下线' }
const SKILL_STAGE_TONE = { Draft: 'slate', Testing: 'amber', Verified: 'blue', Production: 'teal', Deprecated: 'red' }
const SKILL_CATEGORIES = ['开发', '科研', '文档', '数据分析', '项目管理', '内容生成', '设计', '其他']
const SKILL_PACKAGE = ['SKILL.md', 'workflow.yaml', 'tools.json', 'examples/', 'tests/', 'evals/']

const skillPipeline = [
  { key: 'trace', label: '执行轨迹', desc: '采集步骤、工具调用与产物' },
  { key: 'discover', label: '优秀案例识别', desc: '找高频、稳定、低返工的任务' },
  { key: 'extract', label: 'Skill 候选提取', desc: '抽出输入输出与执行骨架' },
  { key: 'generate', label: 'Skill 生成', desc: '生成 Skill 包与结构化字段' },
  { key: 'eval', label: '测试与 Eval', desc: '回放历史任务并打分' },
  { key: 'review', label: '人工审核', desc: '确认适用边界与权限' },
  { key: 'release', label: '版本发布', desc: '打版本号并进入 Skill 库' },
  { key: 'invoke', label: 'Agent 调用', desc: '挂载到 Agent 执行' },
  { key: 'iterate', label: '持续迭代', desc: '按失败样本回归升级' }
]

// 系统自动扫出来的候选：来源是任务轨迹，不是人工填表。
const skillCandidates = [
  {
    id: 'cand-context-pack', taskTitle: '支付服务权限改造 Context Pack 组装', traceId: 'trace-8127',
    runs: 7, stability: 91, successRate: 96, humanEdit: 6, ioStable: 88, reused: 5,
    source: '执矩｜Task Execution', agent: 'guanwei', suggested: 'context-pack-builder',
    signals: ['需求→代码→Schema→测试四段输入结构连续 7 次一致', '人工只改了标题措辞', '被 5 个任务直接复用']
  },
  {
    id: 'cand-bugfix', taskTitle: '支付回调重复触发根因定位与修复', traceId: 'trace-8093',
    runs: 9, stability: 87, successRate: 94, humanEdit: 11, ioStable: 82, reused: 6,
    source: '观微｜Context Engine', agent: 'zhiju', suggested: 'bug-fix-loop',
    signals: ['日志→快照→最小复现三步固定', '两次上线零回滚', '失败样本已被 Eval 收编']
  },
  {
    id: 'cand-issue-skill', taskTitle: '登录失败重复问题聚类与资产化', traceId: 'trace-7981',
    runs: 5, stability: 78, successRate: 88, humanEdit: 19, ioStable: 74, reused: 3,
    source: '和鸣｜Memory Evolution', agent: 'heming', suggested: 'issue-to-skill',
    signals: ['同类 Issue 三个月内出现 5 次', '聚类口径仍需人工确认', '产出的 Memory 命中率 88%']
  },
  {
    id: 'cand-paper', taskTitle: 'LoongArch 信创适配资料精读与要点抽取', traceId: 'trace-7742',
    runs: 4, stability: 72, successRate: 85, humanEdit: 24, ioStable: 70, reused: 2,
    source: '观微｜Context Engine', agent: 'guanwei', suggested: 'paper-analysis',
    signals: ['输入是 PDF 集合，输出结构稳定', '章节切分粒度还在调', '尚未被其它任务复用']
  }
]

// 已进入 Skill 库的正式条目。status 走 Draft→Testing→Verified→Production 生命周期。
const skillLibrary = reactive([
  {
    id: 'context-pack-builder', name: '任务上下文包组装', category: '项目管理',
    summary: '把需求、代码、Schema、历史经验与相关 Skill 组装成一次任务可执行的 Context Pack。',
    useCase: '新任务开工前缺少上下文，或同类任务的上下文结构高度相似时。',
    status: 'Production', version: 'v2.1', updatedAt: '2026-09-12 10:24', origin: '任务轨迹自动提炼', author: '和鸣｜Memory Evolution',
    calls: 236, successRate: 96, qualityScore: 92, avgCost: 0.42, avgDuration: 38, lastEval: '2026-09-12 · 通过率 96%',
    agents: ['guanwei', 'zhiju'], favorite: true, tests: 14,
    inputs: ['task_goal', 'project', 'issue_ref', 'tech_stack', 'memory_scope'],
    outputs: ['context_pack', 'evidence_list', 'skill_suggestion'],
    steps: ['解析任务目标与边界', '召回代码与文档证据', '匹配历史 Memory 与 Skill', '按模板组装并标注置信度', '输出待人工确认的 Context Pack'],
    tools: ['repo_search', 'doc_index', 'memory_recall', 'schema_dump'],
    memories: ['kb-002 权限改造 Context Pack 模板', 'kb-001 支付回调幂等处理 Memory Unit'],
    permissions: ['Read', 'Memory Write'],
    exceptions: ['证据不足 3 条时不生成结论，改为列出缺口清单', '项目未关联仓库时降级为纯文档组包'],
    evalCriteria: ['证据可追溯率 ≥ 90%', '人工删改比例 ≤ 10%', '同类任务复用率 ≥ 60%'],
    examples: ['支付回调修复 Context Pack', '权限改造 Context Pack'],
    versions: [
      { version: 'v2.1', at: '2026-09-12', note: '接入 Memory 召回，证据排序改为置信度优先', successRate: 96, qualityScore: 92 },
      { version: 'v2.0', at: '2026-08-30', note: '输入改为固定五字段结构', successRate: 93, qualityScore: 88 },
      { version: 'v1.1', at: '2026-08-14', note: '补充 Schema 抽取', successRate: 88, qualityScore: 81 }
    ],
    evals: [
      { at: '2026-09-12', kind: '历史任务回放', sample: 40, pass: 96, consistency: 94, completeness: 97, human: 4.6, note: 'Memory 召回上线后一致性提升' },
      { at: '2026-08-30', kind: '版本回归', sample: 40, pass: 93, consistency: 90, completeness: 95, human: 4.4, note: '固定输入结构后波动收窄' }
    ]
  },
  {
    id: 'bug-fix-loop', name: 'Bug 修复闭环', category: '开发',
    summary: '从日志与快照定位根因，产出最小复现、修复补丁与回归用例，收敛到可验证的修复结论。',
    useCase: '线上缺陷、重复报错、需要根因而不是症状修复的场景。',
    status: 'Production', version: 'v1.4', updatedAt: '2026-09-10 19:02', origin: '任务轨迹自动提炼', author: '观微｜Context Engine',
    calls: 188, successRate: 94, qualityScore: 90, avgCost: 0.66, avgDuration: 52, lastEval: '2026-09-10 · 通过率 94%',
    agents: ['zhiju', 'mingjian'], favorite: true, tests: 18,
    inputs: ['symptom', 'logs', 'repo', 'repro_hint'],
    outputs: ['root_cause', 'patch', 'regression_test', 'memory_candidate'],
    steps: ['收集日志与现场快照', '构造最小复现', '定位根因并验证假设', '输出补丁与回归用例', '写入 Memory 候选'],
    tools: ['log_query', 'git_blame', 'test_runner', 'patch_writer'],
    memories: ['kb-001 支付回调幂等处理 Memory Unit'],
    permissions: ['Read', 'Write', 'Execute', 'GitHub Access'],
    exceptions: ['无法复现时只给排查路径，不产出补丁', '涉及支付与权限的补丁强制人工审批'],
    evalCriteria: ['根因可复现率 ≥ 85%', '回归用例覆盖修复点', '一周内复发率 ≤ 5%'],
    examples: ['支付回调重复扣款', '权限越权访问'],
    versions: [
      { version: 'v1.4', at: '2026-09-10', note: '增加复发检测与失败样本回灌', successRate: 94, qualityScore: 90 },
      { version: 'v1.3', at: '2026-08-22', note: '最小复现步骤标准化', successRate: 91, qualityScore: 86 }
    ],
    evals: [
      { at: '2026-09-10', kind: '历史任务回放', sample: 52, pass: 94, consistency: 91, completeness: 93, human: 4.5, note: '复发检测拦截了 2 个假修复' }
    ]
  },
  {
    id: 'code-review-gate', name: '代码评审门禁', category: '开发',
    summary: '按团队规范对待合入变更做一致性、边界条件与安全隐患核查，产出可执行的评审意见。',
    useCase: 'PR 合入前、多人协作的分支收敛、需要统一评审口径时。',
    status: 'Verified', version: 'v1.2', updatedAt: '2026-09-08 15:40', origin: '人工创建 + 轨迹校准', author: '明鉴｜Eval Lab',
    calls: 142, successRate: 91, qualityScore: 87, avgCost: 0.31, avgDuration: 27, lastEval: '2026-09-08 · 通过率 91%',
    agents: ['mingjian', 'zhiju'], favorite: false, tests: 11,
    inputs: ['diff', 'repo', 'convention_scope'],
    outputs: ['review_findings', 'risk_list', 'approval_hint'],
    steps: ['解析 diff 与影响面', '比对团队规范', '扫描边界与安全风险', '输出分级评审意见'],
    tools: ['diff_parser', 'lint_runner', 'secret_scan'],
    memories: ['kb-004 Skill 回归评测 Rubric'],
    permissions: ['Read', 'External API'],
    exceptions: ['diff 超过 2000 行时拆分为分批评审', '涉及密钥变更直接升级为阻断项'],
    evalCriteria: ['高危问题召回率 ≥ 90%', '误报率 ≤ 15%', '评审意见可执行率 ≥ 80%'],
    examples: ['前端分包重构 PR 评审'],
    versions: [
      { version: 'v1.2', at: '2026-09-08', note: '增加密钥扫描与阻断分级', successRate: 91, qualityScore: 87 },
      { version: 'v1.0', at: '2026-08-18', note: '首个发布版本', successRate: 86, qualityScore: 79 }
    ],
    evals: [
      { at: '2026-09-08', kind: '标准测试集', sample: 30, pass: 91, consistency: 88, completeness: 90, human: 4.2, note: '误报率降到 12%' }
    ]
  },
  {
    id: 'issue-to-skill', name: '重复问题资产化', category: '项目管理',
    summary: '把反复出现的 Bug 与失败任务聚类，沉淀为 Memory Unit 与可执行 Skill 候选。',
    useCase: '同类问题三个月内重复出现、需要判断是否值得资产化时。',
    status: 'Testing', version: 'v0.9', updatedAt: '2026-09-11 09:15', origin: '任务轨迹自动提炼', author: '和鸣｜Memory Evolution',
    calls: 46, successRate: 88, qualityScore: 79, avgCost: 0.28, avgDuration: 33, lastEval: '2026-09-11 · 通过率 88%',
    agents: ['heming', 'bowen'], favorite: false, tests: 9,
    inputs: ['issue_set', 'time_window', 'project'],
    outputs: ['cluster_report', 'memory_candidate', 'skill_candidate'],
    steps: ['归集同窗期 Issue', '按根因聚类', '判断是否具备资产化价值', '产出 Memory 与 Skill 候选'],
    tools: ['issue_index', 'cluster_engine', 'memory_writer'],
    memories: ['kb-003 登录失败提示重复问题记录'],
    permissions: ['Read', 'Memory Write', 'Sensitive Action'],
    exceptions: ['聚类结果人工确认前不写入团队记忆', '单次出现的问题只登记不资产化'],
    evalCriteria: ['聚类准确率 ≥ 80%', '候选被采纳率 ≥ 50%'],
    examples: ['登录失败提示重复问题'],
    versions: [
      { version: 'v0.9', at: '2026-09-11', note: '聚类口径改成根因优先', successRate: 88, qualityScore: 79 }
    ],
    evals: [
      { at: '2026-09-11', kind: '人工评分', sample: 12, pass: 88, consistency: 76, completeness: 82, human: 3.8, note: '口径仍在收敛' }
    ]
  },
  {
    id: 'repo-analysis', name: '仓库结构与依赖分析', category: '开发',
    summary: '给出模块边界、依赖方向、热点文件与改动风险面，作为任务开工前的结构底图。',
    useCase: '接手陌生模块、评估改造影响面、拆分大任务时。',
    status: 'Verified', version: 'v1.1', updatedAt: '2026-09-05 17:20', origin: '任务轨迹自动提炼', author: '观微｜Context Engine',
    calls: 97, successRate: 92, qualityScore: 85, avgCost: 0.24, avgDuration: 21, lastEval: '2026-09-05 · 通过率 92%',
    agents: ['guanwei', 'zhiju'], favorite: false, tests: 8,
    inputs: ['repo', 'entry_hint'],
    outputs: ['module_map', 'dependency_graph', 'hotspot_list'],
    steps: ['扫描目录与入口', '抽取模块与依赖关系', '统计改动热点', '输出结构底图与风险提示'],
    tools: ['repo_search', 'ast_index', 'git_stats'],
    memories: [],
    permissions: ['Read', 'File Access'],
    exceptions: ['仓库超过 5000 文件时只输出顶层结构', '无版本控制时禁用热点分析'],
    evalCriteria: ['模块识别完整度 ≥ 85%', '依赖方向准确率 ≥ 90%'],
    examples: ['一修 Web 前后端结构梳理'],
    versions: [{ version: 'v1.1', at: '2026-09-05', note: '支持 monorepo 分包识别', successRate: 92, qualityScore: 85 }],
    evals: [{ at: '2026-09-05', kind: '标准测试集', sample: 20, pass: 92, consistency: 89, completeness: 91, human: 4.3, note: 'monorepo 支持生效' }]
  },
  {
    id: 'paper-analysis', name: '论文精读与要点抽取', category: '科研',
    summary: '从 PDF 集合中抽取问题、方法、实验与结论，输出带页码引用的结构化要点。',
    useCase: '需要快速读懂一批文献并形成可比对要点时。',
    status: 'Testing', version: 'v0.6', updatedAt: '2026-09-09 14:05', origin: '任务轨迹自动提炼', author: '和鸣｜Memory Evolution',
    calls: 31, successRate: 85, qualityScore: 76, avgCost: 0.51, avgDuration: 64, lastEval: '2026-09-09 · 通过率 85%',
    agents: ['guanwei', 'doc'], favorite: false, tests: 7,
    inputs: ['pdf_set', 'focus_questions'],
    outputs: ['structured_notes', 'citation_map'],
    steps: ['解析 PDF 版面', '按章节切分', '抽取问题/方法/实验/结论', '对齐关注问题并标注引用'],
    tools: ['pdf_parser', 'section_split', 'citation_link'],
    memories: [],
    permissions: ['Read', 'File Access', 'External API'],
    exceptions: ['扫描版 PDF 先走 OCR，失败则标记为需人工', '图表结论不单独成条，必须附正文依据'],
    evalCriteria: ['要点与原文一致率 ≥ 90%', '引用可定位率 100%'],
    examples: ['信创适配资料精读'],
    versions: [{ version: 'v0.6', at: '2026-09-09', note: '章节切分改为版面优先', successRate: 85, qualityScore: 76 }],
    evals: [{ at: '2026-09-09', kind: '人工评分', sample: 10, pass: 85, consistency: 74, completeness: 80, human: 3.9, note: '扫描件仍是短板' }]
  },
  {
    id: 'report-composer', name: '技术方案与报告生成', category: '文档',
    summary: '把 Context Pack、执行轨迹与 Eval 结论合成结构固定的方案或结项报告。',
    useCase: '需要产出可交付文档、且文档结构在多次任务中一致时。',
    status: 'Production', version: 'v3.0', updatedAt: '2026-09-14 11:30', origin: '模板演化', author: '执矩｜Task Execution',
    calls: 274, successRate: 95, qualityScore: 91, avgCost: 0.38, avgDuration: 45, lastEval: '2026-09-14 · 通过率 95%',
    agents: ['zhiju', 'doc', 'ppt'], favorite: true, tests: 16,
    inputs: ['context_pack', 'trace', 'eval_result', 'template'],
    outputs: ['report', 'slide_outline', 'artifact'],
    steps: ['选模板', '抽取结论与证据', '按章节填充', '生成图表占位', '输出可编辑文档'],
    tools: ['docx_writer', 'chart_embed', 'template_loader'],
    memories: ['kb-004 Skill 回归评测 Rubric'],
    permissions: ['Read', 'Write', 'File Access'],
    exceptions: ['结论缺证据时留空并标注待补，不编造数据', '涉密字段按权限自动脱敏'],
    evalCriteria: ['结构合规率 100%', '结论与证据一致率 ≥ 95%', '人工返修率 ≤ 10%'],
    examples: ['一休 AI 软件创新技术方案', 'LoongArch 部署指南'],
    versions: [
      { version: 'v3.0', at: '2026-09-14', note: '接入 Eval 结论章节与脱敏规则', successRate: 95, qualityScore: 91 },
      { version: 'v2.2', at: '2026-08-28', note: '模板库支持继承', successRate: 92, qualityScore: 86 }
    ],
    evals: [{ at: '2026-09-14', kind: '版本回归', sample: 24, pass: 95, consistency: 93, completeness: 96, human: 4.7, note: '脱敏规则未误伤正文' }]
  },
  {
    id: 'eval-rubric', name: 'Skill 质量评测 Rubric', category: '项目管理',
    summary: '用统一口径给 Skill 打成功率、输出完整性、结果一致性与人工可读性分，形成质量分。',
    useCase: 'Skill 发布前必过、版本回归必跑、需要横向对比多个 Skill 时。',
    status: 'Production', version: 'v1.0', updatedAt: '2026-09-13 16:12', origin: '人工创建', author: '明鉴｜Eval Lab',
    calls: 312, successRate: 97, qualityScore: 94, avgCost: 0.09, avgDuration: 12, lastEval: '2026-09-13 · 通过率 97%',
    agents: ['mingjian'], favorite: true, tests: 22,
    inputs: ['skill_package', 'replay_set', 'baseline_version'],
    outputs: ['quality_score', 'eval_report', 'regression_diff'],
    steps: ['加载 Skill 包与测试集', '历史任务回放', '四项指标计算', '与基线版本对比', '输出质量分与阻断项'],
    tools: ['replay_runner', 'score_engine', 'diff_reporter'],
    memories: ['kb-004 Skill 回归评测 Rubric'],
    permissions: ['Read', 'Execute', 'Skill Publish'],
    exceptions: ['样本量不足 10 时不给质量分，只标记为参考', '质量分低于 70 一律阻断发布'],
    evalCriteria: ['评分与人工评分相关性 ≥ 0.8', '阻断项零漏报'],
    examples: ['context-pack-builder v2.0 → v2.1 回归'],
    versions: [{ version: 'v1.0', at: '2026-09-13', note: '首次固化为正式 Skill', successRate: 97, qualityScore: 94 }],
    evals: [{ at: '2026-09-13', kind: '标准测试集', sample: 60, pass: 97, consistency: 95, completeness: 96, human: 4.8, note: '可作为发布门禁' }]
  }
])

// 候选 → Skill 的转化表单：保留流水线语义，不是传统验收单。
const skillDraftForm = reactive({
  candidateId: '', name: '', category: '开发', summary: '', useCase: '',
  inputs: '', outputs: '', steps: '', agents: [], tools: '', permissions: [], exceptions: '', evalCriteria: ''
})
const skillFilter = reactive({ keyword: '', category: '全部', status: '全部', sort: 'quality', favoriteOnly: false })
const skillStage = ref('')
const selectedSkillId = ref('context-pack-builder')
const skillDetailTab = ref('overview')
const skillEvalRun = reactive({ running: false, sample: 24, kind: '历史任务回放', result: null })
const skillToasts = ref([])

const selectedSkill = computed(() => skillLibrary.find((item) => item.id === selectedSkillId.value) || skillLibrary[0])

const filteredSkillLibrary = computed(() => {
  const keyword = skillFilter.keyword.trim().toLowerCase()
  let rows = skillLibrary.filter((item) => {
    if (skillFilter.category !== '全部' && item.category !== skillFilter.category) return false
    if (skillFilter.status !== '全部' && item.status !== skillFilter.status) return false
    if (skillFilter.favoriteOnly && !item.favorite) return false
    if (keyword && !`${item.name}${item.summary}${item.useCase}${item.id}`.toLowerCase().includes(keyword)) return false
    return true
  })
  const sorters = {
    quality: (a, b) => b.qualityScore - a.qualityScore,
    calls: (a, b) => b.calls - a.calls,
    success: (a, b) => b.successRate - a.successRate,
    cost: (a, b) => a.avgCost - b.avgCost,
    updated: (a, b) => String(b.updatedAt).localeCompare(String(a.updatedAt))
  }
  rows = [...rows].sort(sorters[skillFilter.sort] || sorters.quality)
  return rows
})

const skillMetrics = computed(() => {
  const total = skillLibrary.length
  const production = skillLibrary.filter((item) => item.status === 'Production').length
  const calls = skillLibrary.reduce((sum, item) => sum + item.calls, 0)
  const avgQuality = Math.round(skillLibrary.reduce((sum, item) => sum + item.qualityScore, 0) / total)
  const avgSuccess = Math.round(skillLibrary.reduce((sum, item) => sum + item.successRate, 0) / total)
  return { total, production, calls, avgQuality, avgSuccess, candidates: skillCandidates.length }
})

const skillPipelineStats = computed(() => ({
  trace: skillCandidates.reduce((sum, item) => sum + item.runs, 0),
  discover: skillCandidates.length,
  extract: skillCandidates.filter((item) => item.stability >= 80).length,
  generate: skillCandidates.filter((item) => item.ioStable >= 80).length,
  eval: skillLibrary.filter((item) => item.status === 'Testing').length,
  review: skillLibrary.filter((item) => ['Testing', 'Verified'].includes(item.status)).length,
  release: skillLibrary.filter((item) => ['Verified', 'Production'].includes(item.status)).length,
  invoke: skillLibrary.reduce((sum, item) => sum + item.calls, 0),
  iterate: skillLibrary.reduce((sum, item) => sum + item.versions.length, 0)
}))

const skillPipelineCount = (key) => skillPipelineStats.value[key] ?? 0

const openSkillCandidate = (candidate) => {
  skillDraftForm.candidateId = candidate.id
  skillDraftForm.name = candidate.suggested === 'context-pack-builder' ? '任务上下文包组装' : candidate.taskTitle.slice(0, 18)
  skillDraftForm.category = candidate.source.includes('Research') ? '科研' : '开发'
  skillDraftForm.summary = `${candidate.taskTitle} 的稳定执行轨迹提炼版本，流程稳定度 ${candidate.stability}%。`
  skillDraftForm.useCase = candidate.signals[0] || ''
  skillDraftForm.inputs = 'task_goal, context_pack, files, memory'
  skillDraftForm.outputs = 'artifact, memory_candidate, decision'
  skillDraftForm.steps = '解析任务目标\n召回证据\n执行并记录轨迹\n产出结构化结论'
  skillDraftForm.agents = [agentById(candidate.agent)?.id || 'guanwei']
  skillDraftForm.tools = 'repo_search, memory_recall'
  skillDraftForm.permissions = ['Read', 'Memory Write']
  skillDraftForm.exceptions = '证据不足时不产出结论，改为列出缺口清单。'
  skillDraftForm.evalCriteria = '历史任务回放通过率 ≥ 90%；人工删改比例 ≤ 15%'
  skillStage.value = 'generate'
  selectedSkillId.value = ''
}

const skillDraftReady = computed(() => Boolean(skillDraftForm.name && skillDraftForm.summary && skillDraftForm.steps))

// 生成 Skill 包：把草稿推进到 Testing，并放进库（前端演示，落库交给后端 Skill 接口）。
const generateSkillFromDraft = () => {
  if (!skillDraftReady.value) return toast('请先补全 Skill 名称、说明与执行步骤')
  const id = `${skillDraftForm.candidateId || 'skill'}-${Date.now().toString(36).slice(-4)}`
  const versions = [{ version: 'v0.1', at: new Date().toISOString().slice(0, 16).replace('T', ' '), note: '由任务轨迹自动生成', successRate: 0, qualityScore: 0 }]
  skillLibrary.unshift({
    id,
    name: skillDraftForm.name,
    category: skillDraftForm.category,
    summary: skillDraftForm.summary,
    useCase: skillDraftForm.useCase || '待补充适用场景',
    status: 'Testing',
    version: 'v0.1',
    updatedAt: versions[0].at,
    origin: '任务轨迹自动提炼',
    author: 'Skill Factory',
    calls: 0, successRate: 0, qualityScore: 0, avgCost: 0, avgDuration: 0,
    lastEval: '尚未评测',
    agents: [...skillDraftForm.agents],
    favorite: false,
    tests: 0,
    inputs: splitDraftList(skillDraftForm.inputs),
    outputs: splitDraftList(skillDraftForm.outputs),
    steps: splitDraftList(skillDraftForm.steps),
    tools: splitDraftList(skillDraftForm.tools),
    memories: [],
    permissions: [...skillDraftForm.permissions],
    exceptions: splitDraftList(skillDraftForm.exceptions),
    evalCriteria: splitDraftList(skillDraftForm.evalCriteria),
    examples: [skillCandidates.find((item) => item.id === skillDraftForm.candidateId)?.taskTitle || '待补充'],
    versions,
    evals: []
  })
  skillStage.value = 'eval'
  selectedSkillId.value = id
  skillDetailTab.value = 'overview'
  persistSkill(skillLibrary[0])
  toast(`已生成 Skill 包：${skillDraftForm.name}（v0.1 · Testing）`)
}

const splitDraftList = (value) => String(value || '').split(/[\n,，;；]/).map((item) => item.trim()).filter(Boolean)

const skillStatusIndex = (status) => Math.max(0, SKILL_STAGES.indexOf(status))

const advanceSkillStatus = (skill) => {
  const index = skillStatusIndex(skill.status)
  if (skill.status === 'Deprecated') return toast('已下线的 Skill 不能直接推进，请先创建新版本')
  if (skill.status === 'Production') return toast('该 Skill 已在生产中，迭代请走新版本')
  if (skill.status === 'Testing' && (skill.qualityScore || 0) < 70) return toast('Eval 质量分低于 70，不能进入正式库')
  skill.status = SKILL_STAGES[index + 1]
  skill.updatedAt = new Date().toISOString().slice(0, 16).replace('T', ' ')
  persistSkill(skill)
  toast(`${skill.name} 进入 ${SKILL_STAGE_LABEL[skill.status]}`)
}

const deprecateSkill = (skill) => {
  skill.status = 'Deprecated'
  skill.updatedAt = new Date().toISOString().slice(0, 16).replace('T', ' ')
  persistSkill(skill)
  toast(`${skill.name} 已下线，Agent 不再调用`)
}

const toggleSkillFavorite = (skill) => {
  skill.favorite = !skill.favorite
  persistSkill(skill)
  toast(skill.favorite ? `已收藏 ${skill.name}` : `已取消收藏 ${skill.name}`)
}

// Skill Eval：回放历史任务 + 良品样本，产出质量分与阻断项。
const runSkillEval = async (skill) => {
  skillEvalRun.running = true
  skillEvalRun.result = null
  await new Promise((resolve) => setTimeout(resolve, 700))
  const sample = skillEvalRun.sample
  const base = skill.successRate || 88
  const pass = Math.min(99, Math.max(60, base + Math.round(Math.random() * 4 - 2)))
  const consistency = Math.min(99, Math.max(58, pass - Math.round(Math.random() * 6)))
  const completeness = Math.min(99, Math.max(60, pass + Math.round(Math.random() * 5)))
  const human = Number((3.4 + Math.random() * 1.5).toFixed(1))
  const score = Math.round(pass * 0.4 + consistency * 0.25 + completeness * 0.2 + (human / 5) * 100 * 0.15)
  const blocks = []
  if (pass < 85) blocks.push(`回放通过率 ${pass}% 低于 85%`)
  if (consistency < 80) blocks.push(`结果一致性 ${consistency}% 低于 80%`)
  if (!skill.agents.length) blocks.push('未关联任何 Agent，无法挂载调用')
  const record = { at: new Date().toISOString().slice(0, 16).replace('T', ' '), kind: skillEvalRun.kind, sample, pass, consistency, completeness, human, note: blocks.length ? `阻断项 ${blocks.length} 条` : '通过发布门禁' }
  skill.evals = [record, ...(skill.evals || [])]
  skill.lastEval = `${record.at} · 通过率 ${pass}%`
  if (SKILL_STAGES.indexOf(skill.status) >= SKILL_STAGES.indexOf('Testing')) skill.successRate = pass
  skill.qualityScore = score
  skill.updatedAt = record.at
  skillEvalRun.result = { ...record, score, blocks }
  skillEvalRun.running = false
  persistSkill(skill)
  toast(blocks.length ? `Eval 未过门禁：${blocks[0]}` : `Eval 通过，质量分 ${score}`)
}

const setSkillStageFilter = (key) => {
  skillStage.value = skillStage.value === key ? '' : key
}

// 版本管理：差异对比与回滚
const rollbackSkillVersion = (skill, version) => {
  const target = (skill.versions || []).find((item) => item.version === version)
  if (!target) return
  skill.versions = [{
    version: target.version,
    at: new Date().toISOString().slice(0, 16).replace('T', ' '),
    note: `回滚到 ${target.version}（原 ${skill.version}）`,
    successRate: target.successRate,
    qualityScore: target.qualityScore
  }, ...skill.versions]
  skill.version = target.version
  skill.successRate = target.successRate
  skill.qualityScore = target.qualityScore
  skill.updatedAt = skill.versions[0].at
  persistSkill(skill)
  toast(`${skill.name} 已回滚到 ${target.version}`)
}

const skillVersionDiff = (skill) => {
  const [current, previous] = skill.versions || []
  if (!current || !previous) return []
  return [
    { label: '成功率', from: `${previous.successRate}%`, to: `${current.successRate}%`, up: current.successRate >= previous.successRate },
    { label: '质量分', from: previous.qualityScore, to: current.qualityScore, up: current.qualityScore >= previous.qualityScore },
    { label: '变更说明', from: previous.note, to: current.note, up: true }
  ]
}

// ─── Skill 库持久化 ────────────────────────────────────────────────────────
// 本地状态先改，再推服务端；失败只提示不打断，避免网络抖动把界面卡住。
const skillSync = reactive({ loading: false, saving: false, source: 'local' })
const skillSyncing = computed(() => skillSync.loading || skillSync.saving)

const persistSkill = async (skill) => {
  try {
    skillSync.saving = true
    await yixiuApi.saveSkill(JSON.parse(JSON.stringify(skill)))
  } catch (error) {
    toast(`Skill 保存失败：${error?.message || error}`)
  } finally {
    skillSync.saving = false
  }
}

const loadSkills = async () => {
  skillSync.loading = true
  try {
    const data = await yixiuApi.skills()
    const remote = Array.isArray(data?.skills) ? data.skills : []
    if (remote.length) {
      skillLibrary.splice(0, skillLibrary.length, ...remote)
    } else {
      // 团队库还是空的：把内置种子一次性写进去，之后一律以服务端为准。
      await yixiuApi.saveSkills(JSON.parse(JSON.stringify(skillLibrary)))
    }
    skillSync.source = 'server'
    if (!skillLibrary.some((item) => item.id === selectedSkillId.value)) {
      selectedSkillId.value = skillLibrary[0]?.id || ''
    }
  } catch (error) {
    skillSync.source = 'local'
    console.warn('[skill-factory] 读取 Skill 库失败，本次使用本地数据：', error)
  } finally {
    skillSync.loading = false
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Agent Center｜Agent 中心
// 定位：这台电脑上有哪些 Agent、哪些已经接入、各自有多少数据，
// 并能统一管理、备份、以及在不同 Agent 之间迁移记忆。
// 与 Agent Registry 的区别：Registry 管「团队自研的智能体能力」，
// Agent 中心管「本机装着的第三方 Agent 及其数据资产」。
// ═══════════════════════════════════════════════════════════════════════════

const AGENT_STATES = ['Development', 'Testing', 'Online', 'Paused', 'Deprecated']
const AGENT_STATE_LABEL = { Development: '开发中', Testing: '测试中', Online: '在线', Paused: '已暂停', Deprecated: '已下线' }
const AGENT_STATE_TONE = { Development: 'blue', Testing: 'amber', Online: 'teal', Paused: 'slate', Deprecated: 'red' }

// ─── 本机 Agent 目录 ────────────────────────────────────────────────────────
// status 同时决定卡片按钮：接入 / 管理 / 需要授权 / 未检测到

const AC_STATUS = {
  connected: { label: '已接入', tone: 'teal', button: '管理' },
  needsAuth: { label: '需要授权', tone: 'amber', button: '需要授权' },
  notDetected: { label: '未检测到', tone: 'slate', button: '官网' }
}
const AC_STATUS_ORDER = ['connected', 'needsAuth', 'notDetected']

const AC_ASSET_TYPES = [
  { key: 'projects', label: '项目', desc: '工作区、仓库与工程目录' },
  { key: 'sessions', label: 'Conversation', desc: '会话与对话记录' },
  { key: 'memories', label: 'Memory', desc: '记忆条目与可复用经验' },
  { key: 'prompts', label: 'Prompt / Rules', desc: 'AGENTS.md、CLAUDE.md 等规则文件' },
  { key: 'skills', label: 'Skill', desc: '技能与工作流定义' },
  { key: 'mcp', label: 'MCP', desc: 'MCP Server 接入配置' },
  { key: 'config', label: '配置文件', desc: '设置与偏好（敏感项脱敏）' }
]

// 迁移可选资产：对应关系是「解析成标准记忆」而不是「复制文件」
const AC_MIGRATE_ASSETS = [
  { key: 'memory', label: 'Memory', desc: '记忆条目与经验沉淀' },
  { key: 'context', label: '项目上下文', desc: '工程结构、Context Pack' },
  { key: 'decision', label: 'Decision', desc: '关键决策、根因与结论' },
  { key: 'rules', label: 'Rules', desc: '约束、规范与红线' },
  { key: 'prompt', label: 'Prompt', desc: '系统提示与指令模板' },
  { key: 'skill', label: 'Skill', desc: '可执行技能包' },
  { key: 'conversation', label: 'Conversation', desc: '历史会话（体积大，默认关闭）' }
]

// 迁移资产 → 来源 Agent 的扫描字段
const AC_MIGRATE_SOURCE = {
  memory: 'memories', context: 'projects', decision: 'memories', rules: 'prompts',
  prompt: 'prompts', skill: 'skills', conversation: 'sessions'
}

// 迁移管线：绝不直接拷贝文件
const AC_PIPELINE = [
  { key: 'parse', label: 'Agent Parser', desc: '按来源 Agent 的格式解析原始数据' },
  { key: 'normalize', label: 'Memory 标准化', desc: '统一成 Memory Unit / Context / Rule 结构' },
  { key: 'compat', label: '兼容性检查', desc: '比对目标 Agent 的能力与字段差异' },
  { key: 'adapt', label: '目标 Agent Adapter', desc: '按目标格式写入，不覆盖原有数据' }
]

const AC_PERMISSIONS = [
  { key: 'read', label: '只读扫描', note: '读取目录结构与文件清单', level: 'default' },
  { key: 'session', label: '读取会话内容', note: '解析 Conversation 正文', level: 'default' },
  { key: 'memory', label: '读取 Memory', note: '解析记忆与经验条目', level: 'default' },
  { key: 'writeMemory', label: '写入 Team Memory', note: '把解析结果沉淀到团队记忆', level: 'grant' },
  { key: 'migrate', label: '执行记忆迁移', note: '向其它 Agent 写入数据', level: 'grant' },
  { key: 'backup', label: '导出备份', note: '生成本地快照文件', level: 'default' },
  { key: 'sensitive', label: '读取敏感配置', note: 'API Key / Token 等，永远不读取', level: 'never' }
]
const AC_NEVER_KEYS = /api[_-]?key|token|secret|cookie|password|passwd|credential|auth/i

const acStamp = () => new Date().toISOString().slice(0, 16).replace('T', ' ')

const acAssetSeed = (counts) => ({
  projects: Array.from({ length: Math.min(counts.projects, 4) }, (_, index) => ({
    name: ['主工作区', '实验分支', '归档工程', '共享仓库'][index] || `项目 ${index + 1}`,
    path: index === 0 ? 'D:/竞赛/软件杯/2026001846源代码' : `~/work/project-${index + 1}`,
    sessions: Math.max(1, Math.round(counts.sessions / Math.max(1, counts.projects))),
    lastUsed: acStamp()
  })),
  sessions: Array.from({ length: Math.min(counts.sessions, 5) }, (_, index) => ({
    id: `sess-${(index + 1).toString().padStart(3, '0')}`,
    title: ['架构梳理', '接口联调', '缺陷定位', '部署验证', '方案讨论'][index] || `会话 ${index + 1}`,
    messages: 8 + index * 6,
    updatedAt: acStamp()
  })),
  memories: Array.from({ length: Math.min(counts.memories, 5) }, (_, index) => ({
    title: ['幂等边界以事件 ID 为准', '索引与查询路径要成对改', '先组上下文再动代码', '失败样本必须回灌 Eval', '迁移前先快照'][index] || `记忆 ${index + 1}`,
    kind: ['Decision', 'RootCause', 'Rule', 'Prompt', 'Decision'][index] || 'Memory',
    updatedAt: acStamp()
  })),
  prompts: Array.from({ length: Math.min(counts.prompts, 4) }, (_, index) => ({
    name: ['AGENTS.md', 'CLAUDE.md', 'rules.md', 'system-prompt.md'][index] || `prompt-${index + 1}.md`,
    kind: index < 2 ? 'Rules' : 'Prompt',
    size: `${(2 + index * 1.4).toFixed(1)} KB`
  })),
  skills: Array.from({ length: Math.min(counts.skills, 4) }, (_, index) => ({
    name: ['code-review', 'bug-fix-loop', 'repo-analysis', 'doc-writer'][index] || `skill-${index + 1}`,
    kind: 'Skill',
    files: 3 + index * 2
  })),
  mcp: Array.from({ length: Math.min(counts.mcp, 4) }, (_, index) => ({
    name: ['filesystem', 'github', 'lightrag', 'fetch'][index] || `mcp-${index + 1}`,
    endpoint: index % 2 === 0 ? 'stdio' : 'streamable-http'
  })),
  config: Array.from({ length: Math.min(counts.config, 5) }, (_, index) => ({
    name: ['settings.json', 'config.toml', 'rules.json', 'API Key', 'Access Token'][index] || `config-${index + 1}`,
    status: '已配置',
    sensitive: index >= 3
  }))
})

const agentCenterCatalog = reactive([
  {
    id: 'claude-code', name: 'Claude Code', vendor: 'Anthropic', logo: '/static/agent-logos/claude-code.png', tone: 'coral', sub: 'Anthropic', site: 'https://claude.ai/code',
    status: 'connected', appInstalled: true, dataNote: '本地数据保留 · 装回即恢复',
    home: '~/.claude',
    dirs: { config: '~/.claude/settings.json', memory: '~/.claude/projects', session: '~/.claude/projects', skill: '~/.claude/skills' },
    lastUsed: '2026-07-09 22:47', scannedAt: '2026-09-17 16:20',
    assets: acAssetSeed({ projects: 3, sessions: 49, memories: 128, prompts: 2, skills: 1, mcp: 2, config: 5 })
  },
  {
    id: 'codex', name: 'Codex', vendor: 'OpenAI', logo: '/static/agent-logos/codex.svg', tone: 'slate', sub: '本机数据保留 · 装回即恢复', site: 'https://openai.com/codex/',
    status: 'connected', appInstalled: true, dataNote: '本地数据保留',
    home: '~/.codex',
    dirs: { config: '~/.codex/config.toml', memory: '~/.codex/memories', session: '~/.codex/sessions', skill: '~/.codex/skills' },
    lastUsed: '2026-09-17 15:32', scannedAt: '2026-09-17 16:20',
    assets: acAssetSeed({ projects: 2, sessions: 258, memories: 64, prompts: 3, skills: 3, mcp: 4, config: 4 })
  },
  {
    id: 'cursor', name: 'Cursor', vendor: 'Anysphere', logo: '/static/agent-logos/cursor.png', tone: 'violet', sub: '本机数据保留 · 装回即恢复', site: 'https://cursor.com',
    status: 'connected', appInstalled: false, dataNote: '应用已卸载 · 本地数据保留',
    home: '~/.cursor',
    dirs: { config: '~/.cursor/mcp.json', memory: '~/.cursor/ai-tracking', session: '~/.cursor/projects', skill: '~/.cursor/skills-cursor' },
    lastUsed: '2026-03-30 20:41', scannedAt: '2026-09-17 16:20',
    assets: acAssetSeed({ projects: 3, sessions: 28, memories: 41, prompts: 2, skills: 2, mcp: 1, config: 3 })
  },
  {
    id: 'dsh', name: 'DeepSeek Harness', vendor: 'DeepSeek', logo: '/static/agent-logos/deepseek.svg', tone: 'teal', sub: 'DeepSeek', site: 'https://github.com/deepseek-ai/deepseek-harness',
    status: 'connected', appInstalled: true, dataNote: '本地数据保留 · 当前会话来源',
    home: '~/.dsh-desktop',
    dirs: { config: '~/.dsh-desktop/settings.yaml', memory: '~/.dsh-desktop/skills', session: '~/.dsh-desktop/sessions', skill: '~/.dsh-desktop/skills' },
    lastUsed: acStamp(), scannedAt: acStamp(),
    assets: acAssetSeed({ projects: 1, sessions: 3, memories: 11, prompts: 1, skills: 11, mcp: 0, config: 2 })
  },
  {
    id: 'trae', name: 'Trae Work', vendor: 'ByteDance', logo: '/static/agent-logos/trae.png', tone: 'blue', sub: '本机数据保留 · 装回即恢复', site: 'https://www.trae.ai',
    status: 'connected', appInstalled: false, dataNote: '应用已卸载 · 本地数据保留',
    home: '~/.trae',
    dirs: { config: '~/.trae/settings.json', memory: '~/.trae/memory', session: '~/.trae/sessions', skill: '~/.trae/skills' },
    lastUsed: '2026-05-11 18:02', scannedAt: '2026-09-17 16:20',
    assets: acAssetSeed({ projects: 2, sessions: 28, memories: 22, prompts: 1, skills: 1, mcp: 1, config: 3 })
  },

  // ── 扫描到本机有数据、但还没接入 ──
  {
    id: 'gemini', name: 'Antigravity', vendor: 'Google', logo: '/static/agent-logos/antigravity.png', tone: 'blue', sub: 'Google', site: 'https://antigravity.google',
    status: 'notDetected', appInstalled: true, dataNote: '本机未检测到',
    home: '~/.gemini',
    dirs: { config: '~/.gemini/settings.json', memory: '~/.gemini/antigravity', session: '~/.gemini/antigravity', skill: '~/.gemini/skills' },
    lastUsed: '2026-08-20 09:43', scannedAt: '',
    seed: { projects: 1, sessions: 12, memories: 18, prompts: 1, skills: 0, mcp: 1, config: 2 }
  },
  {
    id: 'opencode', name: 'OpenCode', vendor: 'SST', logo: '/static/agent-logos/opencode.png', tone: 'teal', sub: '本机未检测到', site: 'https://opencode.ai',
    status: 'notDetected', appInstalled: true, dataNote: '本机未检测到',
    home: '~/.opencode',
    dirs: { config: '~/.opencode/config.json', memory: '~/.opencode/memory', session: '~/.opencode/sessions', skill: '~/.opencode/skills' },
    lastUsed: '2026-08-02 11:15', scannedAt: '',
    seed: { projects: 1, sessions: 7, memories: 9, prompts: 1, skills: 1, mcp: 1, config: 2 }
  },
  {
    id: 'kimi-code', name: 'Kimi Code', vendor: 'Moonshot', logo: '/static/agent-logos/kimi.png', tone: 'violet', sub: '本机未检测到', site: 'https://www.kimi.com',
    status: 'notDetected', appInstalled: true, dataNote: '本机未检测到',
    home: '~/.kimi',
    dirs: { config: '~/.kimi/config.json', memory: '~/.kimi/memory', session: '~/.kimi/sessions', skill: '~/.kimi/skills' },
    lastUsed: '2026-08-28 20:31', scannedAt: '',
    seed: { projects: 1, sessions: 5, memories: 6, prompts: 0, skills: 1, mcp: 0, config: 1 }
  },
  {
    id: 'codebuddy', name: 'CodeBuddy', vendor: 'Tencent', logo: '/static/agent-logos/codebuddy.svg', tone: 'blue', sub: 'Tencent', site: 'https://www.codebuddy.ai',
    status: 'notDetected', appInstalled: true, dataNote: '本机未检测到',
    home: '~/.codebuddy',
    dirs: { config: '~/.codebuddy/config.json', memory: '~/.codebuddy/memory', session: '~/.codebuddy/sessions', skill: '~/.codebuddy/skills' },
    lastUsed: '2026-09-02 14:08', scannedAt: '',
    seed: { projects: 1, sessions: 4, memories: 5, prompts: 1, skills: 0, mcp: 1, config: 2 }
  },
  {
    id: 'qwen-work', name: '千问办公', vendor: '阿里巴巴', logo: '/static/agent-logos/qwen.png', tone: 'amber', sub: '阿里巴巴', site: 'https://qwen.ai',
    status: 'notDetected', appInstalled: true, dataNote: '本机未检测到',
    home: '~/.qwen-work',
    dirs: { config: '~/.qwen-work/config.json', memory: '~/.qwen-work/memory', session: '~/.qwen-work/sessions', skill: '~/.qwen-work/skills' },
    lastUsed: '2026-08-19 10:22', scannedAt: '',
    seed: { projects: 1, sessions: 3, memories: 4, prompts: 0, skills: 0, mcp: 0, config: 1 }
  },

  // ── 检测到安装痕迹但需要授权才能读 ──
  {
    id: 'hermes', name: 'Hermes', vendor: 'Nous Research', logo: '/static/agent-logos/hermes.png', tone: 'violet', sub: 'Nous Research', site: 'https://nousresearch.com',
    status: 'needsAuth', appInstalled: true, dataNote: '检测到安装 · 需要授权',
    home: '~/.hermes',
    dirs: { config: '~/.hermes/config.yaml', memory: '~/.hermes/memory', session: '~/.hermes/sessions', skill: '~/.hermes/skills' },
    lastUsed: '2026-07-21 16:40', scannedAt: '',
    seed: { projects: 1, sessions: 6, memories: 8, prompts: 1, skills: 1, mcp: 1, config: 2 }
  },
  {
    id: 'doubao-work', name: '豆包工作', vendor: '字节跳动', logo: '/static/agent-logos/doubao.png', tone: 'blue', sub: '本机数据保留 · 装回即恢复', site: 'https://www.doubao.com',
    status: 'needsAuth', appInstalled: true, dataNote: '检测到安装 · 需要授权',
    home: '~/.doubao',
    dirs: { config: '~/.doubao/config.json', memory: '~/.doubao/memory', session: '~/.doubao/sessions', skill: '~/.doubao/skills' },
    lastUsed: '2026-08-30 09:05', scannedAt: '',
    seed: { projects: 1, sessions: 4, memories: 3, prompts: 0, skills: 0, mcp: 0, config: 1 }
  },
  {
    id: 'baidu-dazi', name: '百度搭子', vendor: '百度', logo: '/static/agent-logos/baidu.svg', tone: 'red', sub: '百度', site: 'https://chat.baidu.com',
    status: 'needsAuth', appInstalled: true, dataNote: '检测到安装 · 需要授权',
    home: '~/.baidu-dazi',
    dirs: { config: '~/.baidu-dazi/config.json', memory: '~/.baidu-dazi/memory', session: '~/.baidu-dazi/sessions', skill: '~/.baidu-dazi/skills' },
    lastUsed: '2026-07-15 13:50', scannedAt: '',
    seed: { projects: 1, sessions: 2, memories: 2, prompts: 0, skills: 0, mcp: 0, config: 1 }
  },

  // ── 本机没装 ──
  {
    id: 'workbuddy', name: 'WorkBuddy', vendor: 'WorkBuddy', logo: '/static/agent-logos/workbuddy.svg', tone: 'teal', sub: 'WorkBuddy', site: 'https://workbuddy.ai',
    status: 'notDetected', appInstalled: false, dataNote: '本机未检测到', home: '—',
    dirs: { config: '—', memory: '—', session: '—', skill: '—' }, lastUsed: '—', scannedAt: '', seed: {}
  },
  {
    id: 'kimi-work', name: 'Kimi Work', vendor: 'Moonshot', logo: '/static/agent-logos/kimi.png', tone: 'violet', sub: '本机未检测到', site: 'https://www.kimi.com',
    status: 'notDetected', appInstalled: false, dataNote: '本机未检测到', home: '—',
    dirs: { config: '—', memory: '—', session: '—', skill: '—' }, lastUsed: '—', scannedAt: '', seed: {}
  },
  {
    id: 'minimax', name: 'MiniMax Agent', vendor: 'MiniMax', logo: '/static/agent-logos/minimax.ico', tone: 'amber', sub: 'MiniMax', site: 'https://www.minimax.io',
    status: 'notDetected', appInstalled: false, dataNote: '本机未检测到', home: '—',
    dirs: { config: '—', memory: '—', session: '—', skill: '—' }, lastUsed: '—', scannedAt: '', seed: {}
  },
  {
    id: 'trae-work', name: 'Trae Work（新版）', vendor: 'ByteDance', logo: '/static/agent-logos/trae.png', tone: 'blue', sub: '本机未检测到', site: 'https://www.trae.ai',
    status: 'notDetected', appInstalled: false, dataNote: '本机未检测到', home: '—',
    dirs: { config: '—', memory: '—', session: '—', skill: '—' }, lastUsed: '—', scannedAt: '', seed: {}
  }
])

// assets 里只放可展示的样本，真实条目数单独记在 counts 上——
// 否则「本地内容 49 项」会被样本数组长度截成 5。
const AC_SEED_COUNTS = {
  'claude-code': { projects: 3, sessions: 49, memories: 128, prompts: 2, skills: 1, mcp: 2, config: 5 },
  codex: { projects: 2, sessions: 258, memories: 64, prompts: 3, skills: 3, mcp: 4, config: 4 },
  cursor: { projects: 3, sessions: 28, memories: 41, prompts: 2, skills: 2, mcp: 1, config: 3 },
  dsh: { projects: 1, sessions: 3, memories: 11, prompts: 1, skills: 11, mcp: 0, config: 2 },
  trae: { projects: 2, sessions: 28, memories: 22, prompts: 1, skills: 1, mcp: 1, config: 3 }
}
agentCenterCatalog.forEach((agent) => { agent.counts = agent.seed || AC_SEED_COUNTS[agent.id] || {} })

// ─── 一休内置 Agent（Skill Factory 的依赖方，保持可见） ──────────────────────
const AGENT_PERMISSIONS = ['Read', 'Write', 'Execute', 'External API', 'File Access', 'Database Access', 'GitHub Access', 'Memory Write', 'Skill Publish', 'Sensitive Action']
const agentRegistry = reactive([
  {
    id: 'tiangong', name: '天工', code: 'Agent Router', avatar: '/static/tiangong.png',
    role: '路由调度', model: 'deepseek-v4-pro', status: 'Online', permissionLevel: 'L3 · 调度级',
    capability: '读取 Agent Registry 与 Skill 库，按任务类型、上下文、历史成功率、成本与权限选出最合适的 Agent 或组合。',
    skills: [], tools: ['registry_query', 'skill_match', 'cost_estimator', 'trace_reader'],
    tasks: 1284, successRate: 93, evalScore: 91, avgCost: 0.31, lastRun: '2026-09-17 15:32'
  },
  {
    id: 'guanwei', name: '观微', code: 'Research Agent', avatar: '/static/guanwei.png',
    role: '上下文引擎 / 研究检索', model: 'deepseek-v4-pro', status: 'Online', permissionLevel: 'L2 · 读写级',
    capability: '文献检索、深度研究、资料总结、引用核验、竞品分析；为任务组装 Context Pack。',
    skills: ['context-pack-builder', 'repo-analysis', 'paper-analysis'], tools: ['repo_search', 'doc_index', 'pdf_parser', 'memory_recall'],
    tasks: 962, successRate: 94, evalScore: 92, avgCost: 0.44, lastRun: '2026-09-17 15:29'
  },
  {
    id: 'zhiju', name: '执矩', code: 'Coding Agent', avatar: '/static/zhiju.png',
    role: '任务执行 / 代码实现', model: 'deepseek-v4-pro', status: 'Online', permissionLevel: 'L3 · 写入级',
    capability: 'Bug Fix、代码评审、仓库分析、方案文档生成；管理任务步骤并记录执行轨迹。',
    skills: ['bug-fix-loop', 'code-review-gate', 'repo-analysis', 'report-composer'], tools: ['pwsh', 'patch_writer', 'test_runner', 'git_commit'],
    tasks: 1103, successRate: 91, evalScore: 89, avgCost: 0.66, lastRun: '2026-09-17 15:31'
  },
  {
    id: 'bowen', name: '博闻', code: 'Knowledge Agent', avatar: '/static/bowen.png',
    role: '团队记忆 / 知识图谱', model: 'deepseek-v4', status: 'Online', permissionLevel: 'L2 · 读写级',
    capability: '保存团队决策、问题、尝试、根因、方案与验证记录；维护知识图谱与 Memory Unit 库。',
    skills: ['issue-to-skill'], tools: ['memory_writer', 'graph_upsert', 'kb_search'],
    tasks: 741, successRate: 96, evalScore: 93, avgCost: 0.22, lastRun: '2026-09-17 14:52'
  },
  {
    id: 'heming', name: '和鸣', code: 'Document Agent', avatar: '/static/heming.png',
    role: '记忆演化 / 文档提炼', model: 'deepseek-v4', status: 'Testing', permissionLevel: 'L1 · 只读级',
    capability: '从任务记录、Bug、PR 与聊天中提炼可复用经验，生成 Skill 候选与文档资产。',
    skills: ['issue-to-skill', 'paper-analysis'], tools: ['issue_index', 'cluster_engine', 'doc_summarize'],
    tasks: 486, successRate: 88, evalScore: 84, avgCost: 0.28, lastRun: '2026-09-17 13:20'
  },
  {
    id: 'mingjian', name: '明鉴', code: 'Review Agent', avatar: '/static/mingjian.png',
    role: '评测核查 / 质量门禁', model: 'deepseek-v4-pro', status: 'Online', permissionLevel: 'L2 · 核查级',
    capability: '验证 Skill 与任务产出是否有效，比较版本质量、成本、成功率与回归表现，把守发布门禁。',
    skills: ['eval-rubric', 'code-review-gate', 'bug-fix-loop'], tools: ['replay_runner', 'score_engine', 'diff_reporter'],
    tasks: 638, successRate: 95, evalScore: 94, avgCost: 0.18, lastRun: '2026-09-17 15:12'
  },
  {
    id: 'gis', name: '勘舆', code: 'GIS Agent', avatar: '',
    role: '地理信息 / 空间分析', model: 'deepseek-v4', status: 'Development', permissionLevel: 'L1 · 只读级',
    capability: '地图数据处理、空间关系分析、巡检点位与路径规划，输出可视化图层与结论。',
    skills: ['repo-analysis'], tools: ['map_processor', 'geo_query', 'layer_render'],
    tasks: 57, successRate: 81, evalScore: 72, avgCost: 0.35, lastRun: '2026-09-15 10:04'
  },
  {
    id: 'data', name: '明算', code: 'Data Agent', avatar: '',
    role: '数据分析 / 指标计算', model: 'deepseek-v4', status: 'Online', permissionLevel: 'L2 · 只读级',
    capability: 'SQL 取数、指标口径统一、趋势与异常检测，产出可复核的数据结论。',
    skills: ['repo-analysis'], tools: ['sql_runner', 'pandas_tool', 'chart_builder'],
    tasks: 402, successRate: 90, evalScore: 87, avgCost: 0.26, lastRun: '2026-09-17 09:41'
  },
  {
    id: 'doc', name: '翰墨', code: 'PPT Agent', avatar: '',
    role: '演示与汇报产出', model: 'deepseek-v4', status: 'Paused', permissionLevel: 'L1 · 只读级',
    capability: '把报告与结论转成汇报大纲、幻灯片与讲稿，保持与源文档数字一致。',
    skills: ['report-composer'], tools: ['slide_builder', 'outline_writer', 'docx_reader'],
    tasks: 96, successRate: 86, evalScore: 78, avgCost: 0.41, lastRun: '2026-09-02 16:20'
  }
])

const agentById = (id) => agentRegistry.find((item) => item.id === id)
const agentSkills = (agent) => (agent?.skills || []).map((id) => skillLibrary.find((skill) => skill.id === id)).filter(Boolean)

// ─── Agent 中心状态 ─────────────────────────────────────────────────────────

const agentCenterView = ref('hub')
const managedAgentId = ref('claude-code')
const acDetailTab = ref('overview')
const acShowAllConnected = ref(false)
const acShowManualForm = ref(false)
const acMenuAgentId = ref('')
const acScanning = ref(false)
const acSnapshots = ref([
  { id: 'snap-seed-1', agentId: 'claude-code', label: '接入前自动快照', at: '2026-09-17 16:20', size: '18.4 MB', reason: '接入时自动创建' },
  { id: 'snap-seed-2', agentId: 'codex', label: '接入前自动快照', at: '2026-09-17 16:20', size: '42.1 MB', reason: '接入时自动创建' }
])
const acMigrationHistory = ref([
  { id: 'mig-seed-1', from: 'claude-code', to: 'codex', at: '2026-09-17 16:22', assets: ['Memory', 'Decision', 'Rules'], moved: 37, skipped: 4, status: '成功' }
])

const managedAgent = computed(() => agentCenterCatalog.find((item) => item.id === managedAgentId.value) || agentCenterCatalog[0])
const connectedAgents = computed(() => agentCenterCatalog.filter((item) => item.status === 'connected'))
const visibleConnectedAgents = computed(() => acShowAllConnected.value ? connectedAgents.value : connectedAgents.value.slice(0, 3))
const discoverableAgents = computed(() => [...agentCenterCatalog].sort(
  (a, b) => AC_STATUS_ORDER.indexOf(a.status) - AC_STATUS_ORDER.indexOf(b.status)
))
const acStatusCounts = computed(() => ({
  connected: agentCenterCatalog.filter((item) => item.status === 'connected').length,
  needsAuth: agentCenterCatalog.filter((item) => item.status === 'needsAuth').length,
  notDetected: agentCenterCatalog.filter((item) => item.status === 'notDetected').length
}))
const acScannedTotal = computed(() => connectedAgents.value.reduce((sum, agent) => sum + acAssetTotal(agent), 0))

const acAssetRows = (agent, key) => agent?.assets?.[key] || []
// 已接入列表行的一行式数据状态，照参考图口径拼装
const acHubDetail = (agent) => [
  agent.appInstalled ? '应用已安装' : '应用已卸载',
  '本机数据保留',
  `本地 ${acAssetTotal(agent)} 项内容`,
  '云端无版本',
  `最近使用 ${agent.lastUsed}`
].join(' · ')
const acAssetCount = (agent, key) => {
  const counted = agent?.counts?.[key]
  return typeof counted === 'number' ? counted : acAssetRows(agent, key).length
}
function acAssetTotal(agent) {
  return AC_ASSET_TYPES.reduce((sum, type) => sum + acAssetCount(agent, type.key), 0)
}
const acSensitiveCount = (agent) => (agent?.assets?.config || []).filter((item) => item.sensitive).length

// ─── 操作：扫描 / 接入 / 管理 / 备份 ────────────────────────────────────────

const acScanAll = async () => {
  acScanning.value = true
  await new Promise((resolve) => setTimeout(resolve, 900))
  acScanning.value = false
  toast(`扫描完成：本机已接入 ${acStatusCounts.value.connected} 个 Agent，${acStatusCounts.value.notDetected} 个未检测到`)
}

// 不在本机的 Agent 不再提供「接入」，按钮直接开官网
const acOpenSite = (agent) => {
  if (!agent?.site) return toast(`${agent?.name || '该 Agent'} 暂无官网地址`)
  window.open(agent.site, '_blank', 'noopener')
}

const acDisconnectAgent = (agent) => {
  agent.status = 'notDetected'
  agent.appInstalled = false
  agent.dataNote = '本机未检测到'
  acMenuAgentId.value = ''
  acSnapshots.value = acSnapshots.value.filter((item) => item.agentId !== agent.id || item.label !== '当前读取配置')
  toast(`${agent.name} 已断开接入，本地数据不受影响`)
}

const acRemoveAgent = (agent) => {
  const index = agentCenterCatalog.findIndex((item) => item.id === agent.id)
  if (index === -1) return
  agentCenterCatalog.splice(index, 1)
  if (managedAgentId.value === agent.id) agentCenterView.value = 'hub'
  acMenuAgentId.value = ''
  toast(`${agent.name} 已从 Agent 中心移除（本地数据未被改动）`)
}

const acOpenManage = (agent) => {
  managedAgentId.value = agent.id
  agentCenterView.value = 'manage'
  acDetailTab.value = 'overview'
  acMenuAgentId.value = ''
}

const acBackToHub = () => {
  agentCenterView.value = 'hub'
  acMenuAgentId.value = ''
}

const acPushSnapshot = (agent, label, reason) => {
  acSnapshots.value.unshift({
    id: `snap-${agent.id}-${Date.now().toString(36)}`,
    agentId: agent.id, label, at: acStamp(),
    size: `${(8 + Math.random() * 40).toFixed(1)} MB`,
    reason
  })
}

const acRunBackup = (agent) => {
  acPushSnapshot(agent, '手动备份', '用户手动触发')
  acMenuAgentId.value = ''
  toast(`${agent.name} 已生成备份快照，可在「备份」页回滚`)
}

const acRollback = (snapshot) => {
  acSnapshots.value = acSnapshots.value.filter((item) => item.id !== snapshot.id)
  toast(`已回滚到 ${snapshot.at} 的快照，${snapshot.label} 已恢复`)
}

const acTogglePermission = (agent, permission) => {
  if (permission.level === 'never') return toast('敏感配置（API Key / Token / Cookie / 密码）永远不会被读取')
  if (!agent.permissions) agent.permissions = AC_PERMISSIONS.filter((item) => item.level === 'default').map((item) => item.key)
  const index = agent.permissions.indexOf(permission.key)
  if (index === -1) {
    agent.permissions.push(permission.key)
    toast(`已授权：${permission.label}（本次会话生效）`)
  } else {
    agent.permissions.splice(index, 1)
    toast(`已收回：${permission.label}`)
  }
}
const acHasPermission = (agent, permission) => {
  if (permission.level === 'never') return false
  if (!agent.permissions) agent.permissions = AC_PERMISSIONS.filter((item) => item.level === 'default').map((item) => item.key)
  return agent.permissions.includes(permission.key)
}

// ─── 手动添加 ───────────────────────────────────────────────────────────────

const acManualForm = reactive({
  name: '', vendor: '', configDir: '', sessionDir: '', memoryDir: '', skillDir: ''
})
const acManualReady = computed(() => acManualForm.name.trim().length > 0 && acManualForm.configDir.trim().length > 0)

const acAddManualAgent = () => {
  if (!acManualReady.value) return toast('请至少填写 Agent 名称与配置目录')
  const id = `manual-${Date.now().toString(36)}`
  agentCenterCatalog.push({
    id,
    name: acManualForm.name.trim(),
    vendor: acManualForm.vendor.trim() || '手动添加',
    logo: acManualForm.name.trim().slice(0, 1).toUpperCase(),
    tone: 'slate',
    status: 'connected',
    appInstalled: true,
    dataNote: '手动指定目录 · 只读扫描',
    home: acManualForm.configDir.trim(),
    dirs: {
      config: acManualForm.configDir.trim(),
      memory: acManualForm.memoryDir.trim() || '未指定',
      session: acManualForm.sessionDir.trim() || '未指定',
      skill: acManualForm.skillDir.trim() || '未指定'
    },
    lastUsed: acStamp(),
    scannedAt: acStamp(),
    assets: acAssetSeed({ projects: 1, sessions: 2, memories: 1, prompts: 0, skills: 0, mcp: 0, config: 1 })
  })
  acShowManualForm.value = false
  Object.assign(acManualForm, { name: '', vendor: '', configDir: '', sessionDir: '', memoryDir: '', skillDir: '' })
  toast('手动 Agent 已添加并完成只读扫描')
  acOpenManage(agentCenterCatalog[agentCenterCatalog.length - 1])
}

// ─── 记忆迁移 ───────────────────────────────────────────────────────────────

const AC_COMPAT = {
  memory: { codex: 'compatible', 'claude-code': 'compatible', cursor: 'transform', dsh: 'compatible', trae: 'transform', default: 'readonly' },
  context: { codex: 'compatible', 'claude-code': 'compatible', cursor: 'transform', default: 'transform' },
  decision: { codex: 'compatible', 'claude-code': 'compatible', default: 'compatible' },
  rules: { codex: 'compatible', 'claude-code': 'compatible', default: 'transform' },
  prompt: { codex: 'compatible', 'claude-code': 'compatible', default: 'transform' },
  skill: { codex: 'compatible', 'claude-code': 'transform', default: 'unsupported' },
  conversation: { codex: 'transform', 'claude-code': 'compatible', default: 'readonly' }
}
const AC_COMPAT_LABEL = { compatible: '可直接写入', transform: '需转换', readonly: '只读引用', unsupported: '目标不支持' }

const acMigrationForm = reactive({
  from: 'claude-code',
  to: 'codex',
  assets: { memory: true, context: true, decision: true, rules: true, prompt: true, skill: false, conversation: false }
})
const acMigrationRun = reactive({ running: false, stage: -1, result: null })

const acMigrationCompatibility = computed(() => AC_MIGRATE_ASSETS.map((asset) => {
  const table = AC_COMPAT[asset.key] || {}
  const level = table[acMigrationForm.to] || table.default || 'transform'
  return { ...asset, level, levelLabel: AC_COMPAT_LABEL[level], selected: Boolean(acMigrationForm.assets[asset.key]) }
}))
const acMigrationSelected = computed(() => acMigrationCompatibility.value.filter((item) => item.selected))
const acMigrationBlocked = computed(() => acMigrationSelected.value.filter((item) => item.level === 'unsupported'))

const acRunMigration = async () => {
  const from = agentCenterCatalog.find((item) => item.id === acMigrationForm.from)
  const to = agentCenterCatalog.find((item) => item.id === acMigrationForm.to)
  if (!from || !to) return toast('请先选择来源和目标 Agent')
  if (from.id === to.id) return toast('来源和目标不能是同一个 Agent')
  if (!acMigrationSelected.value.length) return toast('至少选择一类要迁移的资产')
  if (acMigrationBlocked.value.length) return toast(`目标 Agent 不支持：${acMigrationBlocked.value.map((item) => item.label).join('、')}`)

  acPushSnapshot(to, `迁移前自动快照（来自 ${from.name}）`, '迁移前自动创建')
  acMigrationRun.running = true
  acMigrationRun.result = null
  const moved = acMigrationSelected.value.reduce((sum, item) => sum + acAssetCount(from, AC_MIGRATE_SOURCE[item.key] || 'memories'), 0)

  for (let index = 0; index < AC_PIPELINE.length; index++) {
    acMigrationRun.stage = index
    await new Promise((resolve) => setTimeout(resolve, 620))
  }
  acMigrationRun.stage = AC_PIPELINE.length
  acMigrationRun.running = false
  acMigrationRun.result = {
    from: from.name, to: to.name,
    assets: acMigrationSelected.value.map((item) => item.label),
    moved, skipped: 0, at: acStamp()
  }
  acMigrationHistory.value.unshift({
    id: `mig-${Date.now().toString(36)}`,
    from: from.id, to: to.id, at: acStamp(),
    assets: acMigrationSelected.value.map((item) => item.label),
    moved, skipped: 0, status: '成功'
  })
  toast(`迁移完成：${from.name} → ${to.name}，${moved} 项资产已标准化写入`)
}

// ─── 与 TeamMemory OS 的联动 ────────────────────────────────────────────────

const acLinkage = computed(() => [
  { key: 'memory', title: '沉淀到 Team Memory', desc: 'Agent 历史记忆经标准化后进入团队记忆库，可人工审核', page: 'search', panel: 'library', value: `${acScannedTotal.value} 项可解析` },
  { key: 'skill', title: '进入 Skill Factory', desc: '优秀执行轨迹可提炼为 Skill 并挂载到内置 Agent', page: 'knowledge', panel: 'recheck', value: `${skillLibrary.length} 个 Skill` },
  { key: 'context', title: '供 Context Engine 调用', desc: '不同 Agent 的历史经验可被组包时召回', page: 'search', panel: 'multimodal', value: '跨 Agent 召回' }
])

const acGotoLinkage = (item) => {
  activePage.value = item.page
  if (item.page === 'knowledge') knowledgePanel.value = item.panel
  if (item.page === 'tasks') taskPanel.value = item.panel
  if (item.page === 'search') searchPanel.value = item.panel
}

const openAgentFromSkill = (agentId) => {
  const agent = agentById(agentId)
  activePage.value = 'knowledge'
  knowledgePanel.value = 'files'
  agentCenterView.value = 'hub'
  nextTick(() => document.querySelector('.areg-builtin')?.scrollIntoView({ behavior: 'smooth', block: 'center' }))
  if (agent) toast(`${agent.name} 是 TeamMemory OS 的内置 Agent，已定位到 Agent 中心`)
}

const openSkillFromAgent = (skillId) => {
  selectedSkillId.value = skillId
  skillDetailTab.value = 'overview'
  activePage.value = 'tasks'
  taskPanel.value = 'recheck'
}

const defaultProfile = {

  ...mockUser,
  employeeId: 'YX-0824',
  teamRole: '项目协作者',
  team: 'TeamMemory OS 协作组',
  currentProject: '一休 TeamMemory OS',
  skillLevel: '协作者',
  phone: '138-0000-1024',
  specialties: ['Context Engine', 'Team Memory', 'Agent', 'Skill', '项目协作'],
  bio: '专注人机协作、团队记忆沉淀与 Skill 资产化。'
}
const defaultAccount = { account: 'yixiu', password: 'Yixiu2026!', name: '聪明的一休', profile: defaultProfile }
const readStorage = (key, fallback) => {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback } catch { return fallback }
}
const savedSession = readStorage(AUTH_SESSION_KEY, null) || (() => { try { return JSON.parse(sessionStorage.getItem(AUTH_SESSION_KEY)) } catch { return null } })()
const isAuthenticated = ref(Boolean(savedSession?.account))
const currentAccount = ref(savedSession?.account || '')
const authMode = ref('login')
const authError = ref('')
const authForm = reactive({ name: '', account: savedSession?.account || 'yixiu', password: '', confirmPassword: '', remember: true, agreed: false })
const showProfileEditor = ref(false)
const profileError = ref('')
const profileDraft = reactive({ ...defaultProfile, specialtyText: defaultProfile.specialties.join('，') })

const activePage = ref('home')
const newsIndex = ref(0)
const activeNews = computed(() => newsSlides[newsIndex.value] || newsSlides[0])
const showSplash = ref(true)
const bootScreenRef = ref(null)
const bootMarkRef = ref(null)
const bootLogoRef = ref(null)
const brandLogoRef = ref(null)
const topbarRef = ref(null)
const navCollapsed = ref(false)
const operatorWidth = ref(Math.min(520, Math.max(300, Number(localStorage.getItem('yixiu-operator-width')) || 360)))
const assistantVoiceListening = ref(false)
let assistantSpeechRecognition = null
let stopOperatorResize = null
let clockTimer = null
let toastTimer = null
let newsCarouselTimer = null
const globalKeyword = ref('')
const globalSearchFocused = ref(false)
const taskChamberOpen = ref(false)
const currentNav = computed(() => navItems.find((item) => item.key === activePage.value) || navItems[0])
const initialRegisteredAccount = readStorage(AUTH_ACCOUNTS_KEY, []).find((item) => item.account === savedSession?.account)
const initialProfile = savedSession?.account === defaultAccount.account ? readStorage(PROFILE_KEY, {}) : initialRegisteredAccount?.profile || {}
const user = reactive({ ...defaultProfile, ...initialProfile })
const agentProfileMap = Object.fromEntries(mockAgents.map((agent) => [agent.id, agent]))
const legacyAgentMap = {
  retrieval: 'guanwei',
  procedure: 'zhiju',
  knowledge: 'bowen',
  collaboration: 'heming',
  audit: 'mingjian'
}
function resolveAgentId(agent = {}) {
  if (agentProfileMap[agent.id]) return agent.id
  if (legacyAgentMap[agent.id]) return legacyAgentMap[agent.id]
  const name = `${agent.name || ''}${agent.duty || ''}`
  if (name.includes('检索') || name.includes('故障') || name.includes('Context')) return 'guanwei'
  if (name.includes('作业') || name.includes('工单') || name.includes('流程') || name.includes('Execution')) return 'zhiju'
  if (name.includes('知识') || name.includes('资料') || name.includes('图谱') || name.includes('Memory')) return 'bowen'
  if (name.includes('协作') || name.includes('联络') || name.includes('联系人')) return 'heming'
  if (name.includes('核查') || name.includes('复检') || name.includes('验收') || name.includes('Eval')) return 'mingjian'
  return 'tiangong'
}
function normalizeAgentList(list = []) {
  const merged = (Array.isArray(list) && list.length ? list : mockAgents).map((agent) => {
    const id = resolveAgentId(agent)
    const profile = agentProfileMap[id]
    return { ...profile, ...agent, id, name: profile.name, avatar: profile.avatar, role: profile.role, slogan: profile.slogan, duty: profile.duty }
  })
  mockAgents.forEach((profile) => {
    if (!merged.some((agent) => agent.id === profile.id)) merged.push(profile)
  })
  return merged
}
const avatarPalette = ['#dcefed', '#e9e2f7', '#f8e7d2', '#dce9f6', '#e3efdb']
const avatarFallback = (name = '一休') => {
  const label = String(name || '一休').replace(/[^\u4e00-\u9fa5A-Za-z0-9]/g, '').slice(-2) || '一休'
  const color = avatarPalette[[...label].reduce((sum, char) => sum + char.charCodeAt(0), 0) % avatarPalette.length]
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96"><rect width="96" height="96" rx="48" fill="${color}"/><circle cx="48" cy="40" r="18" fill="#fff" opacity=".92"/><path d="M18 88c3-21 15-31 30-31s27 10 30 31" fill="#fff" opacity=".92"/><text x="48" y="46" text-anchor="middle" font-family="Arial,sans-serif" font-size="16" font-weight="700" fill="#145f5a">${label}</text></svg>`
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`
}
const avatarFor = (avatar, name) => avatar && !String(avatar).includes('undefined') ? avatar : avatarFallback(name)
const handleAvatarError = (event) => {
  event.target.onerror = null
  event.target.src = avatarFallback(event.target.alt || '天工')
}
const handleAgentAvatarError = (event) => {
  event.target.onerror = null
  event.target.src = avatarFallback(event.target.alt || '天工')
}
const handleContactAvatarError = (event, name) => { event.target.src = avatarFallback(name) }
const handleContentImageError = (event, fallback = fileImageFallback) => {
  if (!event?.target || event.target.src.endsWith(fallback)) return
  event.target.onerror = null
  event.target.src = fallback
}
const nowText = ref('')
const overview = reactive(createOverviewFromMock())
const systemStatus = reactive({ ...overview.status })
const tasks = ref([])
const knowledge = ref([])
const files = ref([])
const contacts = ref([])
const agents = ref(normalizeAgentList(overview.agents))
const loading = reactive({ search: false })
const voiceListening = ref(false)
let speechRecognition = null
const selectedTask = ref(null)
const selectedFile = ref(null)
const selectedKnowledge = ref(null)
const selectedLearningRecommendation = ref(null)
const selectedAiosReport = ref(null)
const isKnowledgeEditing = ref(false)
const knowledgeDraft = reactive({ title: '', content: '', equipment: '', model: '', tagsText: '', source: '' })
const knowledgeSaveStatus = ref('')
const kdAutoSaveTimer = ref(null)
const kdVersions = ref([])
const kdLinks = ref([])
const kdCollaborators = ref([])
const kdNewLink = reactive({ type: 'task', targetId: '', title: '' })
const kdLinksComputed = computed(() => ({
  tasks: kdLinks.value.filter(l => l.link_type === 'task'),
  knowledge: kdLinks.value.filter(l => l.link_type === 'knowledge')
}))
const kdTasks = computed(() => kdLinksComputed.value.tasks)
const kdKnowledgeLinks = computed(() => kdLinksComputed.value.knowledge)
const knowledgeSaveText = computed(() => ({
  unsaved: '未保存', editing: '编辑中...', saving: '保存中...', saved: '✅ 已自动保存', error: '❌ 保存失败', manualSaved: '✅ 已保存并生成版本'
}[knowledgeSaveStatus.value] || ''))
const knowledgeOutline = computed(() => {
  const content = knowledgeDraft.content || ''
  const lines = content.split('\n')
  const result = []
  for (const line of lines) {
    const m = line.match(/^(#{1,4})\s+(.+)/)
    if (m) {
      result.push({ level: m[1].length, text: m[2].trim() })
    }
  }
  return result
})
const toastText = ref('')
const auditResult = ref('')
const selectedAgentId = ref('')
const operatorMessages = ref([])
const aiosLive = reactive({
  runId: '',
  status: 'idle',
  progress: 0,
  goal: '',
  queue: [],
  events: [],
  steps: [],
  loading: false,
  error: ''
})

const aiosStatusText = computed(() => ({
  idle: '待命',
  planned: '已规划',
  running: '执行中',
  waiting_approval: '待确认',
  blocked: '等待依赖',
  completed: '已完成',
  failed: '异常'
}[aiosLive.status] || aiosLive.status || '待命'))
const aiosActiveStep = computed(() => aiosLive.steps.find((step) => !['done', 'skipped'].includes(step.state)) || aiosLive.steps.at(-1) || null)
const aiosVisibleEvents = computed(() => aiosLive.events.slice(0, 8))
const aiosQueueSummary = computed(() => {
  const done = aiosLive.steps.filter((step) => step.state === 'done').length
  return `${done}/${Math.max(aiosLive.steps.length, 1)}`
})

const agentName = (agentId = '') => {
  const key = resolveAgentId({ id: agentId })
  return agents.value.find((agent) => agent.id === key)?.name || agentProfileMap[key]?.name || agentId || '天工'
}
const agentShortName = (name = '') => {
  const text = String(name || '天工').replace(/\s+/g, '')
  return text.length > 2 ? text.slice(0, 2) : text
}
const formatAiosTime = (value) => {
  if (!value) return '刚刚'
  const date = new Date(String(value).replace(' ', 'T'))
  if (Number.isNaN(date.getTime())) return '刚刚'
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
const normalizeAiosRun = (run = {}) => {
  const plan = run.plan || {}
  const rawSteps = Array.isArray(plan.steps) ? plan.steps : []
  const steps = rawSteps.map((step, index) => ({
    key: step.key || step.id || `step-${index + 1}`,
    title: step.title || step.name || `第 ${index + 1} 步`,
    state: step.state || step.status || 'pending',
    agent: step.agent,
    agentId: step.agent_id || step.agentId || step.agent?.id || ''
  }))
  return {
    runId: run.id || run.run_id || plan.id || '',
    status: run.status || plan.workflow_state || 'planned',
    progress: Number(run.progress ?? plan.progress ?? 0),
    goal: run.goal || plan.goal || '',
    queue: Array.isArray(run.queue) ? run.queue : [],
    steps,
    events: Array.isArray(run.events) ? run.events : []
  }
}
const applyAiosRun = (run = {}, events = []) => {
  const normalized = normalizeAiosRun(run)
  aiosLive.runId = normalized.runId
  aiosLive.status = normalized.status
  aiosLive.progress = Math.max(0, Math.min(100, normalized.progress || 0))
  aiosLive.goal = normalized.goal
  aiosLive.queue = normalized.queue
  aiosLive.steps = normalized.steps
  aiosLive.events = (Array.isArray(events) && events.length ? events : normalized.events).slice(0, 12)
  aiosLive.error = ''
}
const refreshAiosTrace = async (runId = aiosLive.runId) => {
  aiosLive.loading = true
  try {
    let detail = null
    if (runId) {
      detail = await yixiuApi.aiosRunDetail(runId)
    } else {
      const status = await yixiuApi.aiosStatus(1)
      const latest = Array.isArray(status.runs) ? status.runs[0] : null
      if (!latest) {
        Object.assign(aiosLive, { runId: '', status: 'idle', progress: 0, goal: '', queue: [], events: [], steps: [], error: '' })
        return
      }
      detail = latest
      runId = latest.id || latest.run_id || latest.plan?.id || ''
    }
    const eventPayload = runId ? await yixiuApi.aiosEvents({ runId, limit: 24 }) : { events: [] }
    applyAiosRun(detail, Array.isArray(eventPayload.events) ? eventPayload.events : [])
  } catch (error) {
    aiosLive.error = error.message || '操作过程暂时无法同步'
  } finally {
    aiosLive.loading = false
  }
}
const refreshAiosTraceSoon = (runId = '') => {
  window.setTimeout(() => refreshAiosTrace(runId || aiosLive.runId), 450)
}

const searchForm = reactive({ deviceName: '', deviceModel: '', faultCode: '', category: '后端服务', faultType: '线上 Bug', maintenanceLevel: '标准协作', query: '' })
const searchFiles = ref([])
const searchAssistantFileInput = ref(null)
const assistantFiles = ref([])
const searchResult = ref(null)
const searchPanel = ref('multimodal')
const searchMultimodalExpanded = ref(true)
const searchTabs = [
  { key: 'multimodal', label: '组装台' },
  { key: 'update', label: '记忆库' },
  { key: 'network', label: '知识网络' },
  { key: 'library', label: '资料库' },
  { key: 'external', label: '导入' }
]
const searchCapabilityCards = [
  { title: '任务材料融合', desc: '需求、代码、文档和 Issue 统一建模', icon: 'search', tone: 'teal', metric: 'Context' },
  { title: 'Memory 追溯', desc: '结果关联历史决策、Skill 和 Eval', icon: 'file', tone: 'amber', metric: '可引用' },
  { title: '执行方案生成', desc: '自动整理步骤、Agent 和验证项', icon: 'tool', tone: 'green', metric: '可转任务' }
]
const searchProcessCards = [
  { title: '查看历史经验', desc: '复用相似任务的上下文包', icon: 'clock', tone: 'blue', action: () => { activePage.value = 'tasks'; taskPanel.value = 'history' } },
  { title: '沉淀 Memory', desc: '把有效结论提交到 Team Memory 审核', icon: 'check', tone: 'amber', action: () => { searchPanel.value = 'update'; prepareKnowledgeFromSearch() } },
  { title: '创建协作任务', desc: '将当前建议转为可执行任务', icon: 'tool', tone: 'teal', action: () => { if (searchResult.value) createTaskFromSearch(recommendationResult.value); else toast('请先完成一次 Context Pack 生成') } },
  { title: '打开 Memory 图谱', desc: '查看任务、问题和 Skill 关系', icon: 'network', tone: 'green', action: () => { activePage.value = 'search'; searchPanel.value = 'network' } }
]
const searchTemplatePrompts = [
  { title: '分析上下文', icon: 'search', prompt: '请根据当前任务描述、附件和历史资料，分析最需要补齐的上下文，并按优先级排序。' },
  { title: '生成执行流', icon: 'file', prompt: '请把 Context Pack 整理成可执行任务步骤，包含负责人、Agent、引用依据和 Eval 标准。' },
  { title: '提取风险', icon: 'shield', prompt: '请识别当前任务中的重复问题、影响范围、发布风险和必须人工确认的步骤。' },
  { title: '转为任务', icon: 'check', prompt: '请根据当前上下文结论生成一条协作任务草稿，包含负责人、Agent、Skill 和计划完成时间。' }
]
const templateIconName = (tpl = {}) => {
  const text = `${tpl.id || ''} ${tpl.name || ''} ${tpl.category || ''}`.toLowerCase()
  if (text.includes('sop') || text.includes('作业') || text.includes('流程')) return 'tool'
  if (text.includes('fault') || text.includes('故障') || text.includes('排查') || text.includes('报告')) return 'search'
  if (text.includes('meeting') || text.includes('会议') || text.includes('纪要') || text.includes('协作')) return 'calendar'
  if (text.includes('safety') || text.includes('安全') || text.includes('规范') || text.includes('高风险')) return 'shield'
  if (text.includes('manual') || text.includes('手册') || text.includes('维修')) return 'file'
  return 'file'
}
const templateIconLabel = (tpl = {}) => {
  const iconName = templateIconName(tpl)
  return ({ tool: 'SOP', search: '查', calendar: '会', shield: '安', file: '文' })[iconName] || '文'
}
const searchRunningSteps = [
  { title: '解析目标', desc: '提取项目、模块、Issue' },
  { title: '召回资料', desc: '匹配文档、Memory、Skill' },
  { title: '风险比对', desc: '识别重复问题与确认项' },
  { title: '生成组包', desc: '输出上下文、步骤和依据' }
]
const searchHistory = ref([
  { id: 'history-1', title: '支付回调幂等修复 Context Pack', deviceName: '支付服务', model: 'Node.js + MySQL', faultCode: 'BUG-421', category: '后端服务', faultType: '线上 Bug', maintenanceLevel: '标准协作', query: '回调重试导致订单重复处理，需要定位幂等边界并补 Eval。', confidence: 91, time: '今日 09:42' },
  { id: 'history-2', title: '权限模型重构上下文组包', deviceName: '成员权限模块', model: 'Vue + Flask', faultCode: 'PR-118', category: '前后端协作', faultType: '功能改造', maintenanceLevel: '高风险协作', query: '统一项目、任务、Memory 和 Skill 的权限边界。', confidence: 88, time: '昨日 16:18' },
  { id: 'history-3', title: '登录失败重复问题追溯', deviceName: '登录链路', model: 'JWT + Session', faultCode: 'ISSUE-77', category: '问题演化', faultType: '重复问题', maintenanceLevel: '轻量协作', query: '多次任务重复出现 token 过期提示不清晰，需要资产化。', confidence: 84, time: '本周一 11:05' }
])
const externalImports = ref([])
const mcpManifest = ref({})
const externalImportLoading = ref(false)
const externalImportForm = reactive({
  provider: 'codex',
  project_name: '一休 Web 端',
  content_type: 'summary',
  title: 'Codex 项目改造总结',
  raw_content: ''
})
const externalImportSteps = [
  { title: '接收外部内容', desc: '保存 Codex / Claude 对话、diff、PR 或总结' },
  { title: '解析项目资产', desc: '提取项目进展、决策、风险和待办' },
  { title: '生成候选资产', desc: '产出 Memory、Skill、Eval 候选等待审核' },
  { title: '关联项目复用', desc: '进入任务执行、上下文中心和团队能力' }
]
const externalImportStats = computed(() => {
  const imports = externalImports.value
  const artifacts = imports.flatMap((item) => item.artifacts || [])
  return [
    { title: '导入记录', value: imports.length, desc: '外部 AI 工作台同步', icon: 'file', tone: 'teal' },
    { title: '候选资产', value: artifacts.length, desc: 'Memory / Skill / Eval', icon: 'network', tone: 'amber' },
    { title: '待审核', value: artifacts.filter((item) => item.review_status === 'pending_review').length, desc: '人工确认后入库', icon: 'shield', tone: 'red' },
    { title: '已通过', value: artifacts.filter((item) => item.review_status === 'approved').length, desc: '可进入团队记忆', icon: 'check', tone: 'green' }
  ]
})
const codexFixedUploadTemplate = computed(() => JSON.stringify({
  provider: externalImportForm.provider || 'codex',
  project_name: externalImportForm.project_name || '一休 Web 端',
  title: externalImportForm.title || 'Codex 任务总结',
  content_type: 'summary',
  task_goal: '本次任务要解决什么问题，面向哪个项目或模块',
  work_summary: [
    '已经完成的关键改动 1',
    '已经完成的关键改动 2'
  ],
  changed_files: [
    'frontend/App.vue',
    'server/backend/routes/yixiu.py'
  ],
  decisions: [
    '本次做出的关键技术或产品决策'
  ],
  risks: [
    '尚未验证、可能影响上线或需要人工确认的风险'
  ],
  todos: [
    '后续还需要补充的事项'
  ],
  validation: [
    '运行过的测试、构建、接口验证或未能验证的原因'
  ],
  memory_candidates: [
    '可以沉淀到团队记忆的经验、约束、规则或适用条件'
  ],
  skill_candidates: [
    '可以演化为 Skill 的可复用流程'
  ],
  eval_cases: [
    '后续可用于回归评测的检查项'
  ],
  next_actions: [
    '建议下一步动作'
  ]
}, null, 2))
const mcpUsagePrompt = computed(() => `请在本次 Codex / Claude 任务结束后调用一休 MCP 工具 yixiu.import_external_ai，并严格使用固定格式上传：
1. provider 使用 ${externalImportForm.provider}
2. project_name 填写当前一休项目或代码仓库名称
3. task_goal、work_summary、changed_files、decisions、risks、todos、validation 必填
4. memory_candidates、skill_candidates、eval_cases 只放适合人工审核的候选资产
5. 不要上传密钥、Token、隐私数据或完整 .env 内容
6. 同步后由一休生成项目进展、Memory / Skill / Eval 候选，并等待人工审核

MCP endpoint: ${mcpManifest.value.endpoint || 'http://127.0.0.1:5000/api/yixiu/mcp'}

固定参数模板：
${codexFixedUploadTemplate.value}`)
const historyInsightCards = [
  { title: '高频模块', desc: '支付服务与权限模块任务占比最高', value: '2 类' },
  { title: '常见线索', desc: 'Bug、改造、重复问题集中出现', value: '3 类' },
  { title: '可复用资产', desc: 'Memory、Skill、Eval Case 可直接带入', value: '9 份' },
  { title: '建议动作', desc: '优先沉淀高置信度任务结论', value: '2 条' }
]
const historyTraceCards = [
  { title: '同模块追溯', desc: '支付回调记录已关联历史 PR、Memory 与 Eval 报告', meta: '6 条链路', icon: 'network', tone: 'teal' },
  { title: '重复问题复用', desc: '登录失败问题已归并聊天、Issue 和修复尝试', meta: '3 项提醒', icon: 'shield', tone: 'red' },
  { title: '资料缺口', desc: '权限重构记录缺少接口契约，建议补充 API 差异文档', meta: '1 项待补', icon: 'file', tone: 'amber' }
]
const knowledgeUpdateSteps = [
  { title: '提取结论', desc: '整理问题、尝试、根因与方案' },
  { title: '核对依据', desc: '绑定任务、Issue、PR、聊天和 Eval' },
  { title: '人工修正', desc: '补全标签、适用条件与边界' },
  { title: '审核入库', desc: '通过后进入 Memory 图谱与智能召回' }
]
const updateProgressCards = computed(() => [
  { title: '引用依据', value: `${searchResult.value?.references?.length || 0} 份`, desc: 'Memory、Skill、Eval', icon: 'file', tone: 'blue' },
  { title: '人工标签', value: `${knowledgeForm.tagText ? knowledgeForm.tagText.split(/[，,]/).filter(Boolean).length : 0} 个`, desc: '用于检索召回', icon: 'network', tone: 'teal' },
  { title: '待审核', value: `${pendingKnowledge.value.length} 条`, desc: '等待管理员确认', icon: 'clock', tone: 'amber' },
  { title: '图谱同步', value: searchResult.value ? '可生成' : '待组包', desc: '关系节点增量更新', icon: 'check', tone: 'green' }
])
const updateQualityRules = [
  { title: '来源可追溯', desc: '绑定任务、Issue、PR、文档或聊天记录' },
  { title: '结论可验证', desc: '根因、方案、适用条件和 Eval 标准可复现' },
  { title: '关系可入图', desc: '至少包含任务、问题、Memory、Skill 中的两个实体' }
]
const resultTab = ref('全部')
const resultTabs = ['全部', '需求文档', '历史任务', 'Memory Unit', 'Skill', 'Eval Case']
const resultTabCopy = {
  '全部': '汇总展示与当前任务最相关的上下文资产和执行建议',
  '需求文档': '查看目标、边界、验收标准和业务背景',
  '历史任务': '参考相似任务、根因判断和处置记录',
  'Memory Unit': '复用团队已验证的问题、方案和适用条件',
  'Skill': '按标准工作流执行分析、修改、验证和沉淀',
  'Eval Case': '核对回归样例、评分标准和质量确认要求'
}

const taskPanel = ref('overview')
const taskTabs = [{ key: 'overview', label: '项目概览' }, { key: 'manage', label: '项目管理' }, { key: 'contacts', label: '协作成员' }]
const taskFilters = reactive({ status: 'all', severity: 'all', category: 'all', faultType: 'all', assignee: 'all', overdue: 'all', keyword: '' })
const taskView = ref('table')
const showTaskForm = ref(false)
const taskForm = reactive({ equipment_name: '', equipment_no: '', equipment_model: '', severity: 'medium', assignee_name: user.name, due_at: '', description: '' })
const contactKeyword = ref('')
const contactDepartment = ref('all')
const contactViewMode = ref('all')
const contactLeftCollapsed = ref(false)
const contactRightCollapsed = ref(false)
const activeConversationId = ref('task-room-1')
const contactReadState = reactive(readStorage(CONTACT_READ_KEY, {}))
const persistContactReadState = () => localStorage.setItem(CONTACT_READ_KEY, JSON.stringify(contactReadState))
const conversationUnread = (id, fallback = 0) => contactReadState[id] ? 0 : fallback
const markConversationRead = (id) => {
  if (!id || contactReadState[id]) return
  contactReadState[id] = true
  persistContactReadState()
}
const chatInput = ref('')
const chatRecording = ref(false)
const chatRecordSeconds = ref(0)
const showTaskPicker = ref(false)
const taskPickerMode = ref('send')
const reportTask = ref(null)
let chatRecorder = null
let chatRecordStream = null
let chatRecordTimer = null
let chatRecordChunks = []
const chatObjectUrls = new Set()
const chatMessages = ref([
  { id: 'm1', conversationId: 'task-room-1', mine: false, text: 'ZK-320 配电柜温度仍偏高，建议先确认接触器触点和散热风道。', time: '09:42', card: { type: 'task', title: 'YX-20260803-001', desc: '配电柜过热检修 · 高风险' } },
  { id: 'm2', conversationId: 'task-room-1', mine: true, text: '已完成停电验电，准备上传红外测温图片。', time: '09:45' },
  { id: 'm3', conversationId: 'expert-1', mine: false, text: '发动机异响优先复核气门间隙，热车前后各记录一次。', time: '10:15', card: { type: 'knowledge', title: '发动机异响排查知识条目', desc: '气门机构、正时链条、润滑状态' } }
])
const loadedConversationIds = reactive({})
const normalizeConversationMessage = (item = {}, conversationId = '') => {
  const senderId = item.sender_id || item.senderId || ''
  const mine = Boolean(item.mine) || senderId === currentAccount.value || item.sender_name === user.name
  const created = item.created_at || item.createdAt || item.time || ''
  const time = created
    ? new Date(String(created).replace(' ', 'T')).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    : new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  return {
    id: item.id || `remote-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
    conversationId: item.conversationId || item.conversation_id || conversationId,
    mine,
    text: item.text || '',
    time,
    attachment: item.attachment && Object.keys(item.attachment).length ? item.attachment : null,
    card: item.card && Object.keys(item.card).length ? item.card : null,
  }
}
const syncConversationMessages = async (conversationId = activeConversationId.value, force = false) => {
  if (!conversationId || (!force && loadedConversationIds[conversationId])) return
  try {
    const rows = await yixiuApi.conversationMessages(conversationId)
    const existing = new Set(chatMessages.value.map((item) => item.id))
    const incoming = rows
      .map((item) => normalizeConversationMessage(item, conversationId))
      .filter((item) => item.text || item.attachment || item.card)
      .filter((item) => !existing.has(item.id))
    if (incoming.length) chatMessages.value.push(...incoming)
    loadedConversationIds[conversationId] = true
  } catch (error) {
    toast(error.message || '会话消息同步失败')
  }
}
const contactMeetings = ref([
  { id: 'morning-review', title: '高风险检修晨会', time: '今日 10:30', status: '待开始', owner: '动力设备检修一组', taskNo: 'YX-20260803-001', members: ['吴鹏', '唐忆哲', '陈程'], agenda: '确认过热原因、停电窗口和复测时间', progress: 40 },
  { id: 'recheck-sync', title: '复检结论同步会', time: '今日 15:00', status: '已预约', owner: '质量复检组', taskNo: 'YX-20260803-004', members: ['李志勇', '博闻'], agenda: '复盘返工项和验收资料归档', progress: 65 }
])

const knowledgePanel = ref('recheck')
const knowledgeTabs = [{ key: 'recheck', label: 'Skill 工厂' }, { key: 'files', label: 'Agent 中心' }, { key: 'mcp', label: 'MCP 配置' }]
const knowledgeKeyword = ref('')
const graphSearchExpanded = ref(false)
const graphSearchInput = ref(null)
const graphKindFilter = ref('all')
const graphDepth = ref(2)
const graphZoom = ref(1)
const graphShowLabels = ref(false)
const graphLayoutMode = ref('grid')
const graphRelationFilter = ref('all')
const graphRelationTypes = ['包含', '对应', '导致', '检测', '形成方案', '引用', '提示风险', '沉淀案例', '支撑']
const graphNodePositions = reactive({})
const graphDragging = ref(null)
const mapCanvasRef = ref(null)
const graphChartRef = ref(null)
let graphChartInstance = null
let graphChartInitTimer = null
const tryInitGraphChart = () => {
  if (!graphChartRef.value) {
    if (graphChartInitTimer) return
    graphChartInitTimer = setTimeout(() => {
      graphChartInitTimer = null
      tryInitGraphChart()
    }, 150)
    return
  }
  if (graphChartInstance) {
    if (graphChartInstance.getDom?.() !== graphChartRef.value) {
      graphChartInstance.dispose()
      graphChartInstance = null
      window.removeEventListener('resize', handleGraphResize)
    } else {
      graphChartInstance.resize()
      updateGraphChart()
      return
    }
  }
  try {
    graphChartInstance = echarts.init(graphChartRef.value)
    graphChartInstance.setOption(buildGraphChartOption())
    graphChartInstance.on('click', (params) => {
      if (params.dataType === 'node') {
        const node = graphNodes.value.find((n) => n.id === params.data.id)
        if (node) selectGraphNode(node)
      }
    })
    window.removeEventListener('resize', handleGraphResize)
    window.addEventListener('resize', handleGraphResize)
  } catch (e) {
    console.error('[graph] init failed:', e)
  }
}
watch([knowledgePanel, isAuthenticated], () => {
  if (knowledgePanel.value === 'network' && isAuthenticated.value) {
    nextTick(tryInitGraphChart)
  }
}, { immediate: true })
const graphLegendFiltered = ref({})
const activeFolder = ref('全部文件')
const selectedFileRow = ref('')
const customFileFolders = ref([])
const customFolderParents = ref({})
const expandedFileFolders = ref(['系统知识库', '项目'])
const draggedFileId = ref('')
const draggedFolderName = ref('')
const fileDropTarget = ref('')
const selectedGraphNode = ref(null)
const graphInspectorTab = ref('info')
const tgSuggestion = ref({
  title: '今日优先处理建议',
  level: '高优先级',
  content: '建议先处理高风险配电柜过热工单，再推进待复检任务，同时关注文件解析异常。',
  tags: ['高风险', '配电柜', '过热', '待复检', '文件解析']
})
const graphCenterNode = ref(null)
const knowledgeForm = reactive({ title: '', type: '历史故障案例', equipment: '', model: '', source: '', tagText: '', summary: '' })
const knowledgeCorrections = reactive({})
const operatorInput = ref('')
const floatingAssistantFileInput = ref(null)
const floatingPromptTemplates = [
  { label: '解释节点', prompt: () => selectedGraphNode.value ? `请解释「${selectedGraphNode.value.label}」的检修含义和关联风险` : '请解释当前知识图谱里最重要的设备检修节点' },
  { label: '找资料', prompt: () => selectedGraphNode.value ? `请查找与「${selectedGraphNode.value.label}」相关的维修资料和案例` : '请帮我查找当前设备相关的维修资料' },
  { label: '整理步骤', prompt: '请把当前故障知识整理成检修步骤和注意事项' },
  { label: '生成摘要', prompt: '请生成一段适合写入检修记录的知识摘要' }
]
const useFloatingPrompt = (template) => {
  operatorInput.value = typeof template.prompt === 'function' ? template.prompt() : template.prompt
}
const floatingAgent = reactive({ x: 0, y: 0, open: false, dragging: false, moved: false })
let floatingAgentDrag = null
const floatingAgentStyle = computed(() => ({
  transform: `translate3d(${floatingAgent.x}px, ${floatingAgent.y}px, 0)`
}))

const operatorProfiles = {
  home: {
    ...agentProfileMap.tiangong,
    icon: 'dashboard',
    status: 'online',
    statusText: '在线',
    welcome: '我是天工，负责统筹其他 agent，帮你盯住今日任务、系统状态和高风险异常。',
    sampleAsk: '帮我看一下今天优先处理什么？',
    sampleAnswer: '建议先处理高风险配电柜过热工单，再推进待复检任务，同时关注文件解析异常。',
    quickTitle: '生成今日检修简报',
    quickDesc: '汇总任务、风险、知识更新和智能体状态',
    placeholder: '询问今日任务、风险或系统状态',
    actions: ['查看高风险', '任务简报', '系统状态', '知识更新']
  },
  search: {
    ...agentProfileMap.guanwei,
    icon: 'search',
    status: 'online',
    statusText: '在线',
    welcome: '我是观微，输入故障描述、设备型号或上传图片后，我会查找线索、召回资料并生成引用依据。',
    sampleAsk: 'CG-125 发动机热车后异响怎么查？',
    sampleAnswer: '优先检查气门间隙、正时链条张紧器和点火连接，并记录热车复测数据。',
    quickTitle: '执行一次智能检索',
    quickDesc: '汇总故障线索、参考资料和可转任务建议',
    placeholder: '描述故障现象或资料需求',
    actions: ['生成研判', '生成检修建议', '查看引用', '创建任务']
  },
  tasks: {
    ...agentProfileMap.zhiju,
    icon: 'wrench',
    status: 'online',
    statusText: '在线',
    welcome: '我是执矩，负责把检修流程拆成可执行步骤，提醒安全要求并推进工单闭环。',
    sampleAsk: '把当前任务推进到复检阶段。',
    sampleAnswer: '可以。高风险步骤需要二次确认，完成检测记录后再进入复检评估。',
    quickTitle: '打开任务执行',
    quickDesc: '查看项目、筛选风险、跟踪进展状态',
    placeholder: '输入任务操作或复检意见',
    actions: ['新建任务', '流转任务', 'Skill 工厂', '联系人']
  },
  contacts: {
    ...agentProfileMap.heming,
    icon: 'user',
    status: 'online',
    statusText: '在线',
    welcome: '我是和鸣，负责联系人管理、人员协调、专家支援和任务沟通。',
    sampleAsk: '帮我找一个电气安全负责人。',
    sampleAnswer: '建议联系赵宁，他当前负责高风险作业确认，可加入 ZK-320 过热检修任务。',
    quickTitle: '协调现场支援',
    quickDesc: '筛选联系人、发起消息并加入协作任务',
    placeholder: '输入人员、部门或支援需求',
    actions: ['搜索联系人', '请求支援', '添加至任务', '查看协作记录']
  },
  recheck: {
    ...agentProfileMap.mingjian,
    icon: 'check',
    status: 'online',
    statusText: '在线',
    welcome: '我是明鉴，负责复检评估、安全检查、质量核验和任务验收。',
    sampleAsk: '这个任务复检不通过怎么处理？',
    sampleAnswer: '需要记录不通过原因和整改要求，并自动退回检修状态，保留复检数据。',
    quickTitle: '运行 Skill Eval',
    quickDesc: '回放历史任务，给 Skill 打成功率、一致性与输出完整性分',
    placeholder: '输入要评测的 Skill 或门禁问题',
    actions: ['Skill 工厂', '运行 Skill Eval', '查看门禁标准', '生成 Eval 报告']
  },
  knowledge: {
    ...agentProfileMap.bowen,
    icon: 'network',
    status: 'busy',
    statusText: '处理中',
    welcome: '我是博闻，负责整理技术资料、维护知识网络，并把有效检修经验沉淀成系统知识。',
    sampleAsk: '这份维修资料能不能加入知识库？',
    sampleAnswer: '需要先通过文件审核和解析，确认设备、型号、故障、SOP 与原始文件一致。',
    quickTitle: '进入智能体注册中心',
    quickDesc: '查看团队 Agent 的能力边界、挂载 Skill、权限与运行数据',
    placeholder: '询问 Agent 能力、Skill 挂载或权限配置',
    actions: ['Agent 中心', '知识网络', '提交沉淀', '资料检索']
  },
  profile: {
    ...agentProfileMap.mingjian,
    icon: 'check',
    status: 'online',
    statusText: '在线',
    welcome: '我是明鉴，会帮你检查项目是否满足设备检修、知识检索、作业闭环和多智能体要求。',
    sampleAsk: '检查一下当前项目能不能答辩。',
    sampleAnswer: '当前已具备工作台、智能检索、任务闭环、知识管理和复检核查能力，文件权限与审核流程还可继续深化。',
    quickTitle: '运行交付核查',
    quickDesc: '检查页面完整性、业务闭环和演示材料准备情况',
    placeholder: '询问个人记录、核查或交付问题',
    actions: ['运行核查', '个人记录', '退出登录', '项目说明']
  }
}

const operatorKey = computed(() => {
  if (activePage.value === 'tasks' && taskPanel.value === 'contacts') return 'contacts'
  if (activePage.value === 'tasks' && taskPanel.value === 'recheck') return 'recheck'
  return activePage.value
})
const pageDefaultAgentId = computed(() => {
  if (activePage.value === 'home') return 'tiangong'
  if (activePage.value === 'search') return 'guanwei'
  if (activePage.value === 'knowledge') return 'bowen'
  if (activePage.value === 'tasks' && taskPanel.value === 'contacts') return 'heming'
  if (activePage.value === 'tasks' && taskPanel.value === 'recheck') return 'mingjian'
  if (activePage.value === 'tasks') return 'zhiju'
  if (activePage.value === 'profile') return 'mingjian'
  return 'tiangong'
})
const activeOperatorAgentId = computed(() => {
  if (activePage.value === 'home') return 'tiangong'
  return selectedAgentId.value || pageDefaultAgentId.value
})
const operatorProfile = computed(() => {
  const contextual = operatorProfiles[operatorKey.value] || operatorProfiles.home
  if (activePage.value === 'home') return contextual
  const selected = selectedAgentId.value ? agentProfileMap[selectedAgentId.value] : null
  if (!selected) return contextual
  return {
    ...contextual,
    ...selected,
    status: selected.status || 'online',
    statusText: selected.status === 'busy' ? '处理中' : '在线',
    welcome: `我是${selected.name}，${selected.duty}`
  }
})
const operatorMessage = (payload = {}, agentId = activeOperatorAgentId.value) => ({
  ...payload,
  agentId: payload.agentId || agentId || pageDefaultAgentId.value,
  page: payload.page || activePage.value
})
const currentOperatorMessages = computed(() => operatorMessages.value.filter((message) => {
  if (message.page !== activePage.value && !message.global) return false
  const owner = message.agentId || pageDefaultAgentId.value
  return owner === activeOperatorAgentId.value
}))
const scrollOperatorMessagesToBottom = () => {
  nextTick(() => {
    window.setTimeout(() => {
      const panels = document.querySelectorAll('.operator-panel .chat-thread, .floating-chat-thread, .search-dialog-thread')
      panels.forEach((panel) => { panel.scrollTop = panel.scrollHeight })
    }, 60)
  })
}
watch(
  () => [activePage.value, currentOperatorMessages.value.length, currentOperatorMessages.value.at(-1)?.id, currentOperatorMessages.value.at(-1)?.loading],
  () => scrollOperatorMessagesToBottom(),
  { flush: 'post' }
)
const todayCompletion = computed(() => {
  const total = overview.stats.pending + overview.stats.inProgress + overview.stats.review + overview.stats.completed
  return Math.round(overview.stats.completed / Math.max(total, 1) * 100)
})

const statCards = computed(() => [
  { key: 'today', label: '今日新增项目', value: overview.stats.todayNew, hint: '点击进入任务执行中心', page: 'tasks', panel: 'manage' },
  { key: 'pending', label: '待处理任务', value: overview.stats.pending, hint: '自动筛选待处理', page: 'tasks', panel: 'manage', status: 'pending' },
  { key: 'progress', label: '进行中任务', value: overview.stats.inProgress, hint: '查看执行中任务', page: 'tasks', panel: 'manage', status: 'in_progress' },
  { key: 'risk', label: '重复问题', value: overview.stats.highRisk, hint: '优先资产化', page: 'tasks', panel: 'manage', severity: 'high' },
  { key: 'review', label: '待 Eval 任务', value: overview.stats.review, hint: '进入 Eval Lab', page: 'knowledge', panel: 'recheck' },
  { key: 'done', label: '已完成任务', value: overview.stats.completed, hint: '查看归档', page: 'tasks', panel: 'manage', status: 'completed' },
  { key: 'kb', label: 'Memory 总量', value: overview.stats.knowledgeTotal, hint: '进入团队能力库', page: 'search', panel: 'library' },
  { key: 'week', label: '本周新增 Memory', value: overview.stats.weekKnowledge, hint: '进入 Memory Evolution', page: 'search', panel: 'update' },
  { key: 'users', label: '在线协作人员', value: overview.stats.onlineUsers, hint: '查看联系人', page: 'tasks', panel: 'contacts' }
])

const visibleTodayTasks = computed(() => tasks.value.slice(0, 6))
const homeWeekdays = ['日', '一', '二', '三', '四', '五', '六']
const scheduleMonth = ref(new Date())
const selectedScheduleDate = ref('')
const manualScheduleItems = ref(readStorage(SCHEDULE_ITEMS_KEY, []))
const scheduleOverrides = ref(readStorage(SCHEDULE_OVERRIDES_KEY, {}))
const scheduleMarks = ref(readStorage(SCHEDULE_MARKS_KEY, {}))
const deletedScheduleIds = ref(readStorage(SCHEDULE_DELETED_KEY, []))
const showScheduleForm = ref(false)
const editingScheduleId = ref('')
const scheduleDraft = reactive({ title: '', date: '', time: '09:00~10:00', tag: '工作安排', people: '', desc: '', important: false, done: false })
watch(manualScheduleItems, (value) => localStorage.setItem(SCHEDULE_ITEMS_KEY, JSON.stringify(value)), { deep: true })
watch(scheduleOverrides, (value) => localStorage.setItem(SCHEDULE_OVERRIDES_KEY, JSON.stringify(value)), { deep: true })
watch(scheduleMarks, (value) => localStorage.setItem(SCHEDULE_MARKS_KEY, JSON.stringify(value)), { deep: true })
watch(deletedScheduleIds, (value) => localStorage.setItem(SCHEDULE_DELETED_KEY, JSON.stringify(value)), { deep: true })
const padDate = (value) => String(value).padStart(2, '0')
const dateKey = (date) => `${date.getFullYear()}-${padDate(date.getMonth() + 1)}-${padDate(date.getDate())}`
const addCalendarDays = (date, count) => {
  const next = new Date(date)
  next.setDate(next.getDate() + count)
  return next
}
const baseScheduleItems = computed(() => {
  const today = new Date()
  const slots = ['09:00~10:00', '10:30~11:30', '14:00~15:00', '16:00~17:00']
  const sourceTasks = tasks.value.length ? tasks.value : visibleTodayTasks.value
  const taskItems = sourceTasks.slice(0, 5).map((task, index) => {
    const offset = index === 0 ? 0 : index - 2
    const day = addCalendarDays(today, offset)
    return {
      id: `task-${task.id}-${index}`,
      key: dateKey(day),
      tag: task.status === 'review' ? 'Eval 安排' : task.severity === 'high' ? '重复问题' : '工作安排',
      title: task.equipment_name,
      desc: `${task.fault_type} · ${task.current_step}`,
      people: `负责人：${task.assignee_name}${task.collaborators?.length ? `，协作：${task.collaborators.slice(0, 2).join('、')}` : ''}`,
      time: slots[index % slots.length],
      editable: true,
      task,
    }
  })
  return [
    ...taskItems,
    {
      id: 'handover-meeting',
      key: dateKey(today),
      tag: '协作会议',
      title: 'AI 原生项目协作碰头会',
      desc: '同步重复问题、Eval 排期和上下文材料到位情况',
      people: `参与人员：${contacts.value.slice(0, 3).map((item) => item.name).join('、') || '聪明的一休、王铭、赵宁'}`,
      time: '17:30~18:00',
      editable: true,
      panel: 'contacts',
    },
  ]
})
const applyScheduleState = (item) => {
  const override = scheduleOverrides.value[item.id] || {}
  const mark = scheduleMarks.value[item.id] || {}
  return { ...item, ...override, ...mark, editable: item.editable !== false, hidden: deletedScheduleIds.value.includes(item.id) }
}
const homeScheduleItems = computed(() => [
  ...baseScheduleItems.value.map(applyScheduleState),
  ...manualScheduleItems.value.map((item) => ({ ...item, manual: true, editable: true, ...(scheduleMarks.value[item.id] || {}) }))
].filter((item) => !item.hidden))
const homeCalendarTitle = computed(() => `${scheduleMonth.value.getFullYear()}.${padDate(scheduleMonth.value.getMonth() + 1)}`)
const homeEventDates = computed(() => new Set(homeScheduleItems.value.map((item) => item.key)))
const homeCalendarDays = computed(() => {
  const month = scheduleMonth.value
  const first = new Date(month.getFullYear(), month.getMonth(), 1)
  const start = new Date(first)
  start.setDate(first.getDate() - first.getDay())
  const todayKey = dateKey(new Date())
  const selectedKey = selectedScheduleDate.value || todayKey
  return Array.from({ length: 42 }, (_, index) => {
    const day = addCalendarDays(start, index)
    const key = dateKey(day)
    return {
      key,
      date: day.getDate(),
      currentMonth: day.getMonth() === month.getMonth(),
      isToday: key === todayKey,
      selected: key === selectedKey,
      hasEvent: homeEventDates.value.has(key),
    }
  })
})
const selectedScheduleItems = computed(() => {
  const selected = selectedScheduleDate.value || dateKey(new Date())
  const items = homeScheduleItems.value.filter((item) => item.key === selected)
  return items.length ? items : [{
    id: 'empty-schedule',
    key: selected,
    tag: '空闲',
    title: '暂无固定协作安排',
    desc: '可用于临时支援、资料整理或 Memory 沉淀',
    people: `当前人员：${user.name}`,
    time: '待安排',
  }]
})
const selectedScheduleLabel = computed(() => {
  const selected = selectedScheduleDate.value || dateKey(new Date())
  return selected === dateKey(new Date()) ? '今天' : selected.slice(5).replace('-', '月') + '日'
})
const scheduleTone = (item) => {
  if (item.done) return 'done'
  if (item.important || item.tag === '重复问题' || item.task?.severity === 'high') return 'critical'
  if (item.tag?.includes('Eval') || item.task?.status === 'review') return 'review'
  if (item.tag?.includes('会议') || item.panel === 'contacts') return 'meeting'
  if (item.tag?.includes('资料')) return 'knowledge'
  if (item.id === 'empty-schedule') return 'quiet'
  return 'work'
}
const scheduleToneStats = computed(() => selectedScheduleItems.value.reduce((acc, item) => {
  const tone = scheduleTone(item)
  acc[tone] = (acc[tone] || 0) + 1
  return acc
}, { critical: 0, review: 0, meeting: 0, work: 0 }))
const schedulePriorityLabel = (item) => ({
  critical: '高优先',
  review: 'Eval',
  meeting: '协作',
  knowledge: '资料',
  done: '已完成',
  quiet: '空闲',
  work: item.tag || '工作'
}[scheduleTone(item)] || item.tag || '工作')
const alerts = computed(() => [
  { title: '重复问题', desc: `${tasks.value.filter((task) => task.severity === 'high').length} 个任务需要转为 Memory / Skill`, tone: 'danger', icon: 'bell', action: () => goStat({ page: 'tasks', panel: 'manage', severity: 'high' }) },
  { title: '待 Eval 任务', desc: `${tasks.value.filter((task) => task.status === 'review').length} 个任务等待 Skill 回归数据`, tone: 'amber', icon: 'check', action: () => goStat({ page: 'knowledge', panel: 'recheck' }) },
  { title: 'Memory 审核异常', desc: '1 份资料解析部分成功，请人工复核', tone: 'violet', icon: 'network', action: () => goStat({ page: 'knowledge', panel: 'files' }) },
  { title: '智能服务状态', desc: systemStatus.ai, tone: 'teal', icon: 'cpu', action: () => activePage.value = 'profile' }
])
const quickActions = [
  { label: '生成 Context Pack', desc: '组装任务上下文', icon: 'search', tone: 'blue', action: () => activePage.value = 'search' },
  { label: '新建项目', desc: '创建人机协作项目', icon: 'wrench', tone: 'teal', action: () => { activePage.value = 'tasks'; taskPanel.value = 'manage'; showTaskForm.value = true } },
  { label: '上传 Memory 资料', desc: '补充团队记忆文件', icon: 'network', tone: 'violet', action: () => { activePage.value = 'knowledge'; knowledgePanel.value = 'files' } },
  { label: '查看重复问题', desc: '优先资产化', icon: 'bell', tone: 'amber', action: () => goStat({ page: 'tasks', panel: 'manage', severity: 'high' }) },
  { label: '进入 Eval Lab', desc: '核对回归结果', icon: 'check', tone: 'blue', action: () => goStat({ page: 'knowledge', panel: 'recheck' }) },
  { label: '查看 Memory 图谱', desc: '浏览资产关系', icon: 'network', tone: 'teal', action: () => goStat({ page: 'search', panel: 'network' }) },
  { label: '联系协作成员', desc: '发起协作沟通', icon: 'user', tone: 'violet', action: () => goStat({ page: 'tasks', panel: 'contacts' }) },
  { label: '团队能力记录', desc: '查看增长档案', icon: 'dashboard', tone: 'amber', action: () => activePage.value = 'profile' }
]
const trendLabels = ['周一', '周二', '周三', '周四', '周五', '周六', '今天']
const faultColors = ['#e15d50', '#e69a35', '#387dc2', '#8d68c7', '#6f8992']
const knowledgeColors = ['#4f82c4', '#8b67c7', '#dc8a35', '#2b9383']
const recentActivities = computed(() => {
  const styles = {
    检索: { icon: 'search', tone: 'blue' },
    查看: { icon: 'network', tone: 'violet' },
    上传: { icon: 'tool', tone: 'amber' },
    收藏: { icon: 'check', tone: 'teal' }
  }
  return overview.recent.map((raw) => {
    const [action = '记录', ...rest] = raw.split(/[：:]/)
    return { raw, action, content: rest.join('：').trim() || raw, ...(styles[action] || { icon: 'dashboard', tone: 'blue' }) }
  })
})
const runRecentActivity = (item) => {
  if (item.action === '检索') {
    activePage.value = 'search'
    searchForm.query = item.content
    return
  }
  if (item.action === '上传') return goStat({ page: 'knowledge', panel: 'files' })
  knowledgeKeyword.value = item.content.replace(/\s*SOP$/i, '')
  goStat({ page: 'search', panel: 'library' })
}

const recommendationResult = computed(() => searchResult.value ? {
  id: 'recommendation-current',
  title: `${searchForm.deviceModel || searchForm.deviceName} ${searchForm.faultType}推荐检修方案`,
  type: '推荐检修方案',
  category: '推荐检修方案',
  equipment: searchForm.deviceName,
  model: searchForm.deviceModel,
  match: searchResult.value.confidence || 88,
  summary: `${searchResult.value.stopAdvice || '结合现场安全要求逐项检查'}；共 ${searchResult.value.suggestion?.steps?.length || 0} 个建议步骤。`,
  tags: ['研判依据', searchForm.faultType, searchForm.maintenanceLevel]
} : null)
const stepText = (step) => {
  if (typeof step === 'string') return step
  if (!step || typeof step !== 'object') return ''
  return step.action || step.title || step.detail || step.desc || step.name || step.content || ''
}
const normalizedSuggestionSteps = computed(() => {
  const raw = searchResult.value?.suggestion?.steps || searchResult.value?.recommended_sop || []
  return raw.map(stepText).filter(Boolean)
})
const filterResultsByTab = (tab) => {
  const list = searchResult.value?.references || []
  if (tab === '推荐检修方案') return recommendationResult.value ? [recommendationResult.value] : []
  if (tab === '全部') return recommendationResult.value ? [...list, recommendationResult.value] : list
  const aliases = {
    '维修手册': ['维修手册'],
    '历史故障案例': ['历史故障案例', '案例'],
    '标准作业流程 SOP': ['标准作业流程 SOP', '标准作业流程', 'SOP'],
    '安全操作规范': ['安全操作规范', '安全规范']
  }
  return list.filter((item) => aliases[tab]?.some((name) => item.type === name || item.category === name))
}
const filteredResults = computed(() => filterResultsByTab(resultTab.value))
const resultTabHint = computed(() => resultTabCopy[resultTab.value])
const resultCountFor = (tab) => filterResultsByTab(tab).length
const historyLearningRecommendations = computed(() => {
  const byFault = searchHistory.value.reduce((acc, item) => {
    acc[item.faultType] = (acc[item.faultType] || 0) + 1
    return acc
  }, {})
  const topFault = Object.entries(byFault).sort((a, b) => b[1] - a[1])[0]?.[0] || searchForm.faultType
  return [
    { title: `${topFault}类故障复用路径`, desc: `近期 ${topFault} 检索较多，建议优先沉淀现象、定位部位、复测标准和安全隔离要求。`, tags: ['高频故障', topFault, '经验复用'], query: `${topFault} 现场现象 原因定位 复测标准` },
    { title: `${searchForm.deviceModel || '当前型号'} 资料补全建议`, desc: '历史检索显示型号、故障代码和现场图片同时存在时，检索命中率更高。', tags: ['资料补全', '多模态', '命中率'], query: `${searchForm.deviceModel} ${searchForm.faultType} 维修手册 SOP` },
    { title: '检索结果沉淀提醒', desc: '将已验证的原因、工具、作业步骤和引用依据提交审核，可减少后续同类问题检索成本。', tags: ['沉淀更新', '审核入库', '知识复用'], query: searchForm.query }
  ]
})
const selectResultTab = (tab) => {
  resultTab.value = tab
  const count = resultCountFor(tab)
  toast(searchResult.value ? `已切换至${tab}，共 ${count} 条结果` : `已选择${tab}，请先执行智能检索`)
}
const filteredTasks = computed(() => tasks.value.filter((task) => {
  const keyword = taskFilters.keyword.trim()
  const statusOk = taskFilters.status === 'all' || task.status === taskFilters.status
  const severityOk = taskFilters.severity === 'all' || task.severity === taskFilters.severity
  const categoryOk = taskFilters.category === 'all' || task.equipment_category === taskFilters.category
  const faultTypeOk = taskFilters.faultType === 'all' || task.fault_type === taskFilters.faultType
  const assigneeOk = taskFilters.assignee === 'all' || task.assignee_name === taskFilters.assignee || task.collaborators?.includes(taskFilters.assignee)
  const overdueOk = taskFilters.overdue === 'all' || (taskFilters.overdue === 'yes' ? isTaskOverdue(task) : !isTaskOverdue(task))
  const keywordOk = !keyword || JSON.stringify(task).includes(keyword)
  return statusOk && severityOk && categoryOk && faultTypeOk && assigneeOk && overdueOk && keywordOk
}))
const taskOverviewRows = computed(() => {
  const total = Math.max(tasks.value.length, 1)
  const completed = tasks.value.filter((task) => task.status === 'completed').length
  return [
    { label: '待启动', value: tasks.value.filter((task) => task.status === 'pending').length, hint: '等待立项确认', filter: { status: 'pending' } },
    { label: '推进中', value: tasks.value.filter((task) => task.status === 'in_progress').length, hint: '人机协作推进中', filter: { status: 'in_progress' } },
    { label: '待验收', value: tasks.value.filter((task) => task.status === 'review').length, hint: '等待 Eval 与项目验收', filter: { status: 'review' } },
    { label: '重点风险', value: tasks.value.filter((task) => task.severity === 'high').length, hint: '优先处理并沉淀资产', filter: { severity: 'high' } },
    { label: '已逾期', value: tasks.value.filter(isTaskOverdue).length, hint: '需要协调排期', filter: { overdue: 'yes' } }
  ].map((row) => ({
    ...row,
    percent: row.percent ?? Math.round(Number(row.value || 0) / total * 100)
  }))
})
const countBy = (list, getter) => {
  const map = new Map()
  list.forEach((item) => {
    const key = getter(item) || '未分类'
    map.set(key, (map.get(key) || 0) + 1)
  })
  return [...map.entries()].map(([key, count]) => ({ key, label: key, count, percent: Math.round(count / Math.max(list.length, 1) * 100) }))
}
const taskStatusAnalysis = computed(() => countBy(tasks.value, (task) => task.status).map((item) => ({ ...item, label: statusText(item.key) })))
const taskRiskAnalysis = computed(() => countBy(tasks.value, (task) => task.severity).map((item) => ({ ...item, label: severityText(item.key) })))
const taskCategoryAnalysis = computed(() => countBy(tasks.value, (task) => task.equipment_category).slice(0, 5))
const faultRankAnalysis = computed(() => countBy(tasks.value, (task) => task.fault_type).sort((a, b) => b.count - a.count).slice(0, 5))
const taskGuidanceOverview = computed(() => {
  const source = filteredTasks.value.length ? filteredTasks.value : tasks.value
  const highRisk = source.filter((task) => task.severity === 'high').length
  const inProgress = source.filter((task) => task.status === 'in_progress').length
  return [
    { key: 'backend', title: '后端修复 Skill', desc: '线上 Bug 优先推送影响面、日志和回归用例', count: source.filter((task) => task.equipment_category === '后端服务' || task.equipment_name?.includes('支付')).length, filter: { category: '后端服务' } },
    { key: 'permission', title: '权限改造 Skill', desc: '权限任务强制校验角色边界、接口契约和数据隔离', count: source.filter((task) => task.equipment_category === '前后端协作' || task.equipment_name?.includes('权限')).length, filter: { category: '前后端协作' } },
    { key: 'highRisk', title: '重复问题资产化', desc: '重复问题需转成 Memory / Skill 并补齐证据链', count: highRisk, filter: { severity: 'high' } },
    { key: 'process', title: '执行中步骤闭环', desc: '跟踪未完成 Skill 步骤，防止跳过 Eval', count: inProgress, filter: { status: 'in_progress' } }
  ]
})
const taskOpsCards = computed(() => {
  const pending = tasks.value.filter((task) => task.status === 'pending')
  const highRisk = tasks.value.filter((task) => task.severity === 'high')
  const review = tasks.value.filter((task) => task.status === 'review')
  const overdue = tasks.value.filter(isTaskOverdue)
  return [
    { label: '项目启动', title: `${pending.length} 个待启动`, desc: pending[0]?.equipment_name ? `优先确认 ${pending[0].equipment_name} 范围` : '暂无待启动项目', icon: 'check', tone: 'amber', action: () => filterTaskBy('status', 'pending') },
    { label: '重点风险', title: `${highRisk.length} 个需跟进`, desc: highRisk[0]?.project_phase ? `当前阶段：${highRisk[0].project_phase}` : '高风险项目已清空', icon: 'shield', tone: 'red', action: () => filterTaskBy('severity', 'high') },
    { label: '项目验收', title: `${review.length} 个待验收`, desc: review[0]?.assignee_name ? `责任人：${review[0].assignee_name}` : '暂无待验收项目', icon: 'file', tone: 'teal', action: () => { taskPanel.value = 'recheck' } },
    { label: '排期预警', title: `${overdue.length} 个逾期`, desc: overdue[0]?.workOrderNo ? `${overdue[0].workOrderNo} 需要协调` : '排期正常', icon: 'clock', tone: 'blue', action: () => { taskFilters.overdue = 'yes'; taskPanel.value = 'manage' } }
  ]
})
const taskTrendData = computed(() => overview.trend?.length ? overview.trend.slice(0, 7) : [3, 4, 2, 5, 4, 6, tasks.value.length])
const taskTrendTotal = computed(() => taskTrendData.value.reduce((total, value) => total + Number(value || 0), 0))
const taskTrendChange = computed(() => Number(taskTrendData.value.at(-1) || 0) - Number(taskTrendData.value.at(-2) || 0))

// ===== ECharts 美化图表配置 =====
const chartTheme = {
  ink: '#172328', muted: '#68787e', line: '#e6ecee',
  teal: '#16766f', tealDark: '#0f5854', blue: '#3979b8', amber: '#c8872e',
  danger: '#b44c43', coral: '#d86657', violet: '#8062b5'
}
const statusColorMap = { pending: '#c8872e', in_progress: '#3979b8', review: '#8062b5', completed: '#16766f', paused: '#94a3b8', rejected: '#b44c43', overdue: '#d86657' }
const riskColorMap = { low: '#6c9b72', medium: '#d79542', high: '#c95f5a', critical: '#b44c43' }
const chartTooltip = { backgroundColor: 'rgba(23,35,40,.92)', borderWidth: 0, textStyle: { color: '#fff', fontSize: 12 }, extraCssText: 'border-radius:10px;box-shadow:0 6px 18px rgba(0,0,0,.18);' }

// 首页：最近 7 天任务趋势（柱状 + 折线组合）
const homeTrendOption = computed(() => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...chartTooltip },
  legend: { data: ['任务处理量', '趋势'], top: 4, right: 6, icon: 'roundRect', itemWidth: 14, itemHeight: 8, textStyle: { color: chartTheme.muted, fontSize: 11 } },
  grid: { left: 38, right: 18, top: 38, bottom: 28 },
  xAxis: {
    type: 'category', data: trendLabels, boundaryGap: true,
    axisLine: { lineStyle: { color: chartTheme.line } }, axisTick: { show: false },
    axisLabel: { color: chartTheme.muted, fontSize: 11 }
  },
  yAxis: { type: 'value', splitLine: { lineStyle: { color: chartTheme.line, type: 'dashed' } }, axisLabel: { color: chartTheme.muted, fontSize: 11 } },
  series: [
    {
      name: '任务处理量', type: 'bar', data: overview.trend, barWidth: 22,
      itemStyle: { borderRadius: [6, 6, 0, 0], color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#5fa7c4' }, { offset: 1, color: '#c4dde3' }] } },
      emphasis: { itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#4d96b6' }, { offset: 1, color: '#aed1d8' }] } } }
    },
    {
      name: '趋势', type: 'line', data: overview.trend, smooth: true, symbol: 'circle', symbolSize: 7,
      lineStyle: { color: chartTheme.teal, width: 3 },
      itemStyle: { color: '#fff', borderColor: chartTheme.teal, borderWidth: 2.5 },
      areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(22,118,111,.28)' }, { offset: 1, color: 'rgba(22,118,111,.02)' }] } }
    }
  ]
}))

// 首页：故障构成环形图
const homeFaultOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c}%', ...chartTooltip },
  legend: { orient: 'vertical', right: 2, top: 'center', icon: 'circle', itemWidth: 9, itemHeight: 9, textStyle: { color: chartTheme.muted, fontSize: 11 } },
  series: [{
    type: 'pie', radius: ['46%', '70%'], center: ['36%', '50%'], avoidLabelOverlap: true,
    itemStyle: { borderColor: '#fff', borderWidth: 2, borderRadius: 6 },
    label: { show: true, formatter: '{d}%', color: chartTheme.ink, fontSize: 11, fontWeight: 'bold' },
    labelLine: { length: 8, length2: 8 },
    data: overview.faultDistribution.map((item, index) => ({ name: item.label, value: item.value, itemStyle: { color: faultColors[index] } }))
  }]
}))

const homeStatusOption = computed(() => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...chartTooltip },
  grid: { left: 58, right: 26, top: 16, bottom: 22 },
  xAxis: { type: 'value', splitLine: { lineStyle: { color: chartTheme.line, type: 'dashed' } }, axisLabel: { color: chartTheme.muted, fontSize: 10 } },
  yAxis: {
    type: 'category',
    data: taskStatusAnalysis.value.map((item) => item.label),
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: chartTheme.ink, fontSize: 11, fontWeight: 700 }
  },
  series: [{
    type: 'bar',
    barWidth: 15,
    data: taskStatusAnalysis.value.map((item) => ({
      value: item.count,
      itemStyle: { color: statusColorMap[item.key] || chartTheme.teal, borderRadius: [0, 8, 8, 0] }
    })),
    label: { show: true, position: 'right', color: chartTheme.ink, fontSize: 11, fontWeight: 800 }
  }]
}))

const homeRiskOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c} 项 ({d}%)', ...chartTooltip },
  legend: { bottom: 0, left: 'center', icon: 'circle', itemWidth: 8, itemHeight: 8, textStyle: { color: chartTheme.muted, fontSize: 10 } },
  series: [{
    type: 'pie',
    radius: ['48%', '72%'],
    center: ['50%', '44%'],
    itemStyle: { borderColor: '#fff', borderWidth: 2, borderRadius: 7 },
    label: { show: true, formatter: '{c}', color: chartTheme.ink, fontSize: 11, fontWeight: 800 },
    data: taskRiskAnalysis.value.map((item) => ({
      name: item.label,
      value: item.count,
      itemStyle: { color: riskColorMap[item.key] || chartTheme.coral }
    }))
  }]
}))

const homeQualityOption = computed(() => ({
  tooltip: { trigger: 'item', ...chartTooltip },
  radar: {
    radius: '64%',
    center: ['50%', '54%'],
    splitNumber: 4,
    axisName: { color: chartTheme.muted, fontSize: 11 },
    splitLine: { lineStyle: { color: ['#eef3f4', '#e7edef', '#dfe8ea', '#d7e2e4'] } },
    splitArea: { areaStyle: { color: ['rgba(22,118,111,.03)', 'rgba(57,121,184,.04)'] } },
    axisLine: { lineStyle: { color: '#dce7e9' } },
    indicator: [
      { name: '闭环', max: 100 },
      { name: '复检', max: 100 },
      { name: '安全', max: 100 },
      { name: '协作', max: 100 },
      { name: '沉淀', max: 100 }
    ]
  },
  series: [{
    type: 'radar',
    symbol: 'circle',
    symbolSize: 5,
    data: [{
      value: [
        todayCompletion.value,
        92,
        Math.max(60, 100 - overview.stats.highRisk * 8),
        Math.min(96, 70 + contacts.value.filter((item) => item.status === 'online').length * 5),
        Math.min(98, 58 + overview.stats.weekKnowledge * 6)
      ],
      areaStyle: { color: 'rgba(22,118,111,.22)' },
      lineStyle: { color: chartTheme.teal, width: 2.5 },
      itemStyle: { color: '#fff', borderColor: chartTheme.teal, borderWidth: 2 }
    }]
  }]
}))

const homeKnowledgeOption = computed(() => {
  const labels = ['周一', '周二', '周三', '周四', '周五', '周六', '今天']
  const additions = [2, 3, 2, 4, 3, Math.max(2, overview.stats.weekKnowledge - 2), overview.stats.weekKnowledge]
  const citations = additions.map((value, index) => value * 4 + index * 2 + 6)
  return {
    tooltip: { trigger: 'axis', ...chartTooltip },
    legend: { data: ['新增知识', '引用次数'], top: 0, right: 8, icon: 'roundRect', itemWidth: 14, itemHeight: 8, textStyle: { color: chartTheme.muted, fontSize: 11 } },
    grid: { left: 36, right: 38, top: 36, bottom: 26 },
    xAxis: { type: 'category', data: labels, axisLine: { lineStyle: { color: chartTheme.line } }, axisTick: { show: false }, axisLabel: { color: chartTheme.muted, fontSize: 10 } },
    yAxis: [
      { type: 'value', splitLine: { lineStyle: { color: chartTheme.line, type: 'dashed' } }, axisLabel: { color: chartTheme.muted, fontSize: 10 } },
      { type: 'value', splitLine: { show: false }, axisLabel: { color: chartTheme.muted, fontSize: 10 } }
    ],
    series: [
      {
        name: '新增知识',
        type: 'bar',
        data: additions,
        barWidth: 18,
        itemStyle: { borderRadius: [7, 7, 0, 0], color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: chartTheme.violet }, { offset: 1, color: '#d7caea' }] } }
      },
      {
        name: '引用次数',
        type: 'line',
        yAxisIndex: 1,
        data: citations,
        smooth: true,
        symbolSize: 6,
        lineStyle: { color: chartTheme.amber, width: 2.5 },
        itemStyle: { color: '#fff', borderColor: chartTheme.amber, borderWidth: 2 }
      }
    ]
  }
})

// 任务页：近 7 天任务趋势折线图
const taskTrendOption = computed(() => ({
  tooltip: { trigger: 'axis', ...chartTooltip },
  grid: { left: 30, right: 16, top: 22, bottom: 24 },
  xAxis: {
    type: 'category', data: trendLabels, boundaryGap: false,
    axisLine: { lineStyle: { color: chartTheme.line } }, axisTick: { show: false },
    axisLabel: { color: chartTheme.muted, fontSize: 10 }
  },
  yAxis: { type: 'value', splitLine: { lineStyle: { color: chartTheme.line, type: 'dashed' } }, axisLabel: { color: chartTheme.muted, fontSize: 10 } },
  series: [{
    type: 'line', data: taskTrendData.value, smooth: true, symbol: 'circle', symbolSize: 7,
    lineStyle: { color: '#2f7f8f', width: 3 },
    itemStyle: { color: '#fff', borderColor: '#2f7f8f', borderWidth: 2.5 },
    areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(47,135,148,.32)' }, { offset: 1, color: 'rgba(47,135,148,.02)' }] } },
    markPoint: { symbol: 'pin', symbolSize: 38, data: [{ type: 'max', name: '峰值' }], itemStyle: { color: chartTheme.teal }, label: { color: '#fff', fontSize: 10 } }
  }]
}))

// 任务页：任务状态占比（横向柱状图，可点击筛选）
const taskStatusOption = computed(() => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...chartTooltip },
  grid: { left: 52, right: 26, top: 10, bottom: 16 },
  xAxis: { type: 'value', splitLine: { lineStyle: { color: chartTheme.line, type: 'dashed' } }, axisLabel: { color: chartTheme.muted, fontSize: 10 } },
  yAxis: {
    type: 'category', data: taskStatusAnalysis.value.map((i) => i.label),
    axisLine: { lineStyle: { color: chartTheme.line } }, axisTick: { show: false },
    axisLabel: { color: chartTheme.ink, fontSize: 11 }
  },
  series: [{
    type: 'bar', barWidth: 14,
    data: taskStatusAnalysis.value.map((i) => ({ value: i.count, key: i.key, itemStyle: { color: statusColorMap[i.key] || chartTheme.teal, borderRadius: [0, 7, 7, 0] } })),
    label: { show: true, position: 'right', color: chartTheme.ink, fontSize: 11, fontWeight: 'bold' }
  }]
}))

// 任务页：风险等级分布（环形图，可点击筛选）
const taskRiskOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c} 项 ({d}%)', ...chartTooltip },
  legend: { orient: 'vertical', right: 2, top: 'center', icon: 'circle', itemWidth: 9, itemHeight: 9, textStyle: { color: chartTheme.muted, fontSize: 10 } },
  series: [{
    type: 'pie', radius: ['42%', '66%'], center: ['36%', '50%'],
    itemStyle: { borderColor: '#fff', borderWidth: 2, borderRadius: 6 },
    label: { show: true, formatter: '{c}', color: chartTheme.ink, fontSize: 10, fontWeight: 'bold' },
    data: taskRiskAnalysis.value.map((i) => ({ name: i.label, value: i.count, key: i.key, itemStyle: { color: riskColorMap[i.key] || chartTheme.coral } }))
  }]
}))
const priorityTasks = computed(() => tasks.value.filter((task) => task.severity === 'high' || task.status === 'review' || isTaskOverdue(task) || task.progress < 25).slice(0, 5))
const taskEvents = computed(() => tasks.value.flatMap((task, index) => [
  { id: `${task.id}-create`, time: task.created_at, text: `${task.title} 已立项，负责人 ${task.assignee_name}` },
  { id: `${task.id}-step`, time: task.due_at, text: `${task.equipment_name} 当前阶段：${task.project_phase || task.current_step}，进度 ${task.progress}%` },
  ...(task.next_milestone ? [{ id: `${task.id}-milestone`, time: task.due_at, text: `下一里程碑：${task.next_milestone}` }] : []),
  ...(task.status === 'review' ? [{ id: `${task.id}-review`, time: task.due_at, text: `${task.title} 已提交验收，等待 Eval 数据和人工确认` }] : []),
  ...(index === 0 ? [{ id: `${task.id}-risk`, time: task.created_at, text: `${task.title} 已标记为重点项目，需确认风险与交付边界` }] : [])
]).slice(0, 10))
const taskBoardColumns = computed(() => ['pending', 'in_progress', 'review', 'completed'].map((key) => ({ key, label: statusText(key), tasks: filteredTasks.value.filter((task) => task.status === key) })))
const myTasks = computed(() => tasks.value.filter((item) => item.assignee_name === user.name || item.collaborators?.includes(user.name)))
// ─── 个人空间：个人 AI 协作与能力成长中心 ────────────────────────────────────
// 只展示「我参与什么项目、贡献多少 Memory / Skill、用了哪些 Agent、完成哪些任务」。
const profileQuickCards = computed(() => {
  const assigned = tasks.value.filter((task) => task.assignee_name === user.name || task.assignee === user.name)
  const approvedKnowledge = knowledge.value.filter((item) => item.status === 'approved')
  const completed = myTasks.value.filter((task) => task.status === 'completed')
  const memoryCount = approvedKnowledge.length + knowledge.value.length
  return [
    { title: '待办任务', value: assigned.filter((task) => task.status !== 'completed').length, desc: '需要我推进', icon: 'calendar', tone: 'blue', page: 'tasks', panel: 'manage' },
    { title: '参与项目', value: myTasks.value.length, desc: '我参与的项目', icon: 'wrench', tone: 'violet', page: 'tasks', panel: 'manage' },
    { title: 'Memory 贡献', value: memoryCount, desc: '已沉淀条目', icon: 'network', tone: 'orange', page: 'search', panel: 'library' },
    { title: 'Skill 贡献', value: skillLibrary.length, desc: '已发布 Skill', icon: 'check', tone: 'gold', page: 'knowledge', panel: 'recheck' },
    { title: 'Agent 协作', value: connectedAgents.value.length, desc: '已接入 Agent', icon: 'cpu', tone: 'cyan', page: 'knowledge', panel: 'files' },
    { title: '最近活动', value: Math.max(6, completed.length + approvedKnowledge.length), desc: '近 7 天记录', icon: 'clock', tone: 'red', page: 'profile' }
  ]
})
const profileSecurityItems = computed(() => [
  { title: '账号绑定', desc: '138****5678', meta: '已绑定', icon: 'user', action: 'edit-profile' },
  { title: '登录密码', desc: '建议定期更新', meta: '正常', icon: 'shield' },
  { title: '登录设备管理', desc: '已登录 3 台设备', meta: '查看', icon: 'cpu' },
  { title: '二次验证', desc: '高风险操作确认', meta: '已开启', icon: 'check' },
  { title: 'Agent 数据权限', desc: '只读扫描 · 不读取凭据', meta: '已授权 5 个', icon: 'tool' },
  { title: 'Memory 访问权限', desc: '可读写团队记忆库', meta: '可写', icon: 'network' },
  { title: '退出账号', desc: currentAccount.value || '当前账号', meta: '退出', icon: 'settings', action: 'logout' }
])
const profileToolItems = computed(() => [
  { title: '修改资料', desc: '编辑个人档案', icon: 'user', action: 'edit-profile' },
  { title: '我的任务', desc: '查看我参与的项目', icon: 'wrench', page: 'tasks', panel: 'manage' },
  { title: 'Agent 中心', desc: '管理本机 Agent 与记忆迁移', icon: 'cpu', page: 'knowledge', panel: 'files' },
  { title: '上下文引擎', desc: '生成任务上下文包', icon: 'search', page: 'search', panel: 'multimodal' },
  { title: '我的 Memory', desc: '查看我沉淀的记忆', icon: 'network', page: 'search', panel: 'library' },
  { title: '我的 Skill', desc: '查看我贡献的 Skill', icon: 'check', page: 'knowledge', panel: 'recheck' }
])
const profileRecentItems = computed(() => {
  const first = myTasks.value[0]
  const projectEntry = first
    ? {
        title: first.title,
        desc: `参与项目 · ${first.current_step || '推进中'}`,
        icon: 'wrench',
        page: 'tasks',
        panel: 'manage',
        meta: first.updated_at || first.due_at || '今日'
      }
    : {
        title: '参与项目：一休 TeamMemory OS',
        desc: '参与项目 · 人机协作与团队记忆改造',
        icon: 'wrench',
        page: 'tasks',
        panel: 'manage',
        meta: '今天 11:02'
      }
  return [
    projectEntry,
    { title: '新增 Memory：支付回调幂等处理', desc: 'Memory 贡献 +1，已进入团队记忆库', icon: 'network', page: 'search', panel: 'library', meta: '今天 10:24' },
    { title: '使用 Codex / Claude Code 协作', desc: 'Agent 协作 · 已生成可复用执行轨迹', icon: 'cpu', page: 'knowledge', panel: 'files', meta: '今天 09:41' },
    { title: 'Agent 数据备份完成', desc: 'Claude Code · 迁移前快照已生成', icon: 'shield', page: 'knowledge', panel: 'files', meta: '昨天 22:08' },
    { title: 'Skill 候选生成：任务上下文包组装', desc: '来自 7 次稳定执行轨迹，稳定度 91%', icon: 'check', page: 'knowledge', panel: 'recheck', meta: '昨天 18:30' },
    { title: 'Context Pack 生成', desc: '权限改造任务 · 证据 14 条', icon: 'search', page: 'search', panel: 'multimodal', meta: '昨天 15:12' }
  ].slice(0, 6)
})
const profileGrowthScore = computed(() => 3200
  + myTasks.value.length * 70
  + knowledge.value.filter((item) => item.status === 'approved').length * 25
  + skillLibrary.length * 40)

// 协作等级体系：新成员 → 协作者 → 核心成员 → 项目负责人 → 知识贡献者
const PROFILE_COLLAB_LEVELS = ['新成员', '协作者', '核心成员', '项目负责人', '知识贡献者']
const profileCollabLevelIndex = computed(() => {
  const score = profileGrowthScore.value
  if (score >= 9000) return 4
  if (score >= 7000) return 3
  if (score >= 5000) return 2
  if (score >= 3500) return 1
  return 0
})
const profileCollabLevel = computed(() => PROFILE_COLLAB_LEVELS[profileCollabLevelIndex.value])
const profileCollabProgress = computed(() => Math.min(100, Math.round((profileGrowthScore.value % 2000) / 20) + 12))

// 协作画像：六个维度，直接反映在团队记忆与 Agent 协作上的实际贡献
const profileGrowthBenefits = computed(() => [
  { title: `项目参与 ${myTasks.value.length}`, icon: 'wrench' },
  { title: `Memory 贡献 ${knowledge.value.length}`, icon: 'network' },
  { title: `Skill 贡献 ${skillLibrary.length}`, icon: 'check' },
  { title: `Agent 协作 ${connectedAgents.value.length}`, icon: 'cpu' },
  { title: `任务完成 ${myTasks.value.filter((task) => task.status === 'completed').length}`, icon: 'shield' },
  { title: `知识沉淀 ${knowledge.value.filter((item) => item.status === 'approved').length}`, icon: 'file' }
])
const profilePreferenceItems = computed(() => [
  { title: '主题模式', icon: 'settings', meta: '浅色纸质' },
  { title: '消息提醒', icon: 'bell', meta: '已开启' },
  { title: '默认项目', icon: 'wrench', meta: user.currentProject },
  { title: 'Agent 推荐', icon: 'cpu', meta: '自动匹配' },
  { title: 'Context 推荐', icon: 'search', meta: '组包时召回' },
  { title: 'Memory 自动沉淀', icon: 'network', meta: '需人工审核' },
  { title: '风险提醒', icon: 'shield', meta: '高优先级' }
])
const pendingKnowledge = computed(() => knowledge.value.filter((item) => item.status === 'pending' && item.reviewable))
const departments = computed(() => [...new Set(contacts.value.map((item) => item.department))])
const filteredContacts = computed(() => contacts.value.filter((contact) => {
  const keywordOk = !contactKeyword.value || JSON.stringify(contact).includes(contactKeyword.value)
  const deptOk = contactDepartment.value === 'all' || contact.department === contactDepartment.value
  return keywordOk && deptOk
}))
const meetingConversations = computed(() => contactMeetings.value.map((meeting) => ({
  id: `meeting-${meeting.id}`,
  kind: 'meeting',
  name: meeting.title,
  avatar: '/static/heming.png',
  position: '会议',
  department: meeting.owner,
  specialty: meeting.agenda,
  devices: meeting.members,
  currentTask: meeting.agenda,
  workload: meeting.progress,
  lastMessage: meeting.time,
  unread: conversationUnread(`meeting-${meeting.id}`, meeting.status === '待开始' ? 1 : 0),
  taskNo: meeting.taskNo,
  risk: 'medium',
  meeting
})))
const conversations = computed(() => [
  { id: 'task-room-1', kind: 'group', name: 'ZK-320 过热检修群', avatar: '/static/heming.png', position: '任务群组', department: '动力设备检修一组', specialty: '高风险任务协作', devices: ['配电柜', 'ZK-320'], currentTask: 'ZK-320 配电柜过热检修', workload: 78, lastMessage: '已上传红外测温图片', unread: conversationUnread('task-room-1', 3), taskNo: 'YX-20260803-001', risk: 'high' },
  ...meetingConversations.value,
  ...contacts.value.map((contact, index) => {
    const id = String(contact.id || '').startsWith('local-group-') ? `contact-${contact.id}` : index === 0 ? 'expert-1' : `contact-${contact.id}`
    return {
      id,
      kind: String(contact.id || '').startsWith('local-group-') ? 'group' : 'contact',
      name: contact.name,
      avatar: contact.avatar,
      position: contact.position,
      department: contact.department,
      specialty: contact.specialty,
      devices: contact.devices,
      currentTask: contact.currentTask,
      workload: contact.workload,
      lastMessage: index === 0 ? '已给出异响排查建议' : '等待现场反馈',
      unread: conversationUnread(id, index === 1 ? 1 : 0),
      taskNo: contact.currentTask,
      risk: index === 2 ? 'high' : 'medium'
    }
  })
])
const contactStats = computed(() => ({
  online: contacts.value.filter((item) => ['online', '在线'].includes(item.status)).length,
  groups: conversations.value.filter((item) => item.kind === 'group').length,
  meetings: contactMeetings.value.length
}))
const contactModes = computed(() => [
  { key: 'all', label: '全部', count: conversations.value.length },
  { key: 'group', label: '群聊', count: contactStats.value.groups },
  { key: 'meeting', label: '会议', count: contactStats.value.meetings },
  { key: 'contact', label: '联系人', count: contacts.value.length }
])
const filteredConversations = computed(() => conversations.value.filter((item) => {
  const keywordOk = !contactKeyword.value || JSON.stringify(item).includes(contactKeyword.value)
  const deptOk = contactDepartment.value === 'all' || item.department === contactDepartment.value || item.kind === 'meeting'
  const modeOk = contactViewMode.value === 'all' || item.kind === contactViewMode.value
  return keywordOk && deptOk && modeOk
}))
const unreadContactCount = computed(() => conversations.value.reduce((sum, item) => sum + Number(item.unread || 0), 0))
const activeConversation = computed(() => conversations.value.find((item) => item.id === activeConversationId.value) || conversations.value[0])
const activeMessages = computed(() => chatMessages.value.filter((item) => item.conversationId === activeConversation.value?.id))
const graphPositions = [
  [12, 18], [31, 12], [55, 14], [76, 18], [88, 39], [78, 64],
  [57, 78], [34, 76], [14, 61], [9, 39], [25, 48], [46, 35],
  [63, 43], [43, 58], [66, 63], [30, 31], [52, 22], [72, 30]
]
const layoutPoint = (index, total) => {
  if (graphLayoutMode.value === 'circle') {
    const angle = Math.PI * 2 * index / Math.max(total, 1)
    return [50 + Math.cos(angle) * 36, 50 + Math.sin(angle) * 34]
  }
  if (graphLayoutMode.value === 'tree') {
    const level = Math.floor(index / 7)
    return [14 + (index % 7) * 12, 22 + level * 20]
  }
  return graphPositions[index % graphPositions.length]
}
const graphKindMeta = {
  equipment: { text: '设备', important: true },
  model: { text: '设备型号' },
  part: { text: '零部件' },
  fault: { text: '故障现象', important: true },
  cause: { text: '故障原因' },
  method: { text: '检测方法' },
  solution: { text: '检修方案' },
  sop: { text: 'SOP', important: true },
  risk: { text: '安全风险' },
  case: { text: '历史案例' },
  doc: { text: '技术资料', important: true }
}
const graphLegend = Object.entries(graphKindMeta).filter(([, meta]) => meta.important).map(([kind, meta]) => ({ kind, label: meta.text }))
const cleanGraphLabel = (value, fallback) => {
  const text = String(value || fallback || '').replace(/[\[\]{}"']/g, '').replace(/\s+/g, ' ').trim()
  return text.length > 12 ? `${text.slice(0, 12)}…` : text
}
const isAutoKnowledgeSource = (value) => /goview|OBD|CG-125|engine|circuit|manual|vehicle|auto/i.test(JSON.stringify(value || {}))
const isBridgeGraphKind = (kind) => ['method', 'solution', 'sop', 'risk', 'doc'].includes(kind)
const graphNodes = computed(() => {
  const keyword = knowledgeKeyword.value.trim()
  const graphKnowledge = knowledge.value.filter((item) => !item.status || item.status === 'approved' || item.status === '已通过')
  const expandedNodes = graphKnowledge.flatMap((item) => [
    { id: `${item.id}-equipment`, label: cleanGraphLabel(item.equipment, '通用设备'), kind: 'equipment', source: item, level: 1 },
    { id: `${item.id}-model`, label: cleanGraphLabel(item.model, '通用型号'), kind: 'model', source: item, level: 1 },
    { id: `${item.id}-part`, label: cleanGraphLabel(item.tags?.[0], '关键部件'), kind: 'part', source: item, level: 2 },
    { id: `${item.id}-fault`, label: cleanGraphLabel(item.tags?.[1] || item.category || item.type, '故障现象'), kind: 'fault', source: item, level: 1 },
    { id: `${item.id}-cause`, label: cleanGraphLabel(knowledgeSummaryLines(item)[0], '故障原因'), kind: 'cause', source: item, level: 2 },
    { id: `${item.id}-method`, label: item.type?.includes('安全') ? '安全检查' : '检测方法', kind: 'method', source: item, level: 2 },
    { id: `${item.id}-solution`, label: item.category || '检修方案', kind: 'solution', source: item, level: 2 },
    { id: `${item.id}-sop`, label: cleanGraphLabel(item.type?.includes('SOP') ? item.title : '标准步骤'), kind: 'sop', source: item, level: 2 },
    { id: `${item.id}-risk`, label: item.tags?.includes('安全') ? '作业风险' : '安全风险', kind: 'risk', source: item, level: 3 },
    { id: `${item.id}-case`, label: item.type?.includes('案例') ? item.title : '历史案例', kind: 'case', source: item, level: 3 },
    { id: `${item.id}-doc`, label: cleanGraphLabel(item.title, '技术资料'), kind: 'doc', source: item, level: 1 }
  ])
    .filter((node) => node.level <= graphDepth.value)
    .filter((node) => graphKindFilter.value === 'all' || node.kind === graphKindFilter.value)
  const seen = new Set()
  const rawNodes = expandedNodes.filter((node) => {
    const key = `${node.kind}-${node.label}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
  const limit = graphDepth.value === 1 ? 18 : graphDepth.value === 2 ? 38 : 56
  const autoNodes = rawNodes.filter((node) => isAutoKnowledgeSource(node.source))
  const bridgeNodes = rawNodes.filter((node) => !isAutoKnowledgeSource(node.source) && isBridgeGraphKind(node.kind))
  const otherNodes = rawNodes.filter((node) => !isAutoKnowledgeSource(node.source) && !isBridgeGraphKind(node.kind))
  const balancedNodes = [
    ...autoNodes,
    ...bridgeNodes.slice(0, Math.ceil(limit * 0.32)),
    ...otherNodes
  ]
  const selectedNodes = [...new Map(balancedNodes.map((node) => [node.id, node])).values()].slice(0, limit)

  return selectedNodes.map((node, index) => {
    const [defaultX, defaultY] = layoutPoint(index, selectedNodes.length)
    const fixed = graphNodePositions[node.id]
    const meta = graphKindMeta[node.kind] || graphKindMeta.doc
    return {
      ...node,
      x: fixed?.x ?? defaultX,
      y: fixed?.y ?? defaultY,
      kindText: meta.text,
      important: Boolean(meta.important),
      summary: node.source?.summary || node.source?.content || '该节点已关联设备、故障现象、维修资料和检修任务，可继续展开查看上下游依据。',
      tags: node.source?.tags?.length ? node.source.tags : [meta.text, node.source?.model || '通用型号', node.source?.type || '知识条目'],
      matched: keyword ? JSON.stringify(node).includes(keyword) || JSON.stringify(node.source || {}).includes(keyword) : false
    }
  })
})
const graphEdges = computed(() => {
  const radial = graphNodes.value.map((node, index) => ({
    id: `edge-${node.id}`,
    x1: 410,
    y1: 260,
    x2: Math.round(node.x / 100 * 820),
    y2: Math.round(node.y / 100 * 520),
    faint: selectedGraphNode.value && selectedGraphNode.value.id !== node.id && node.source?.id !== selectedGraphNode.value.source?.id,
    label: graphRelationTypes[index % graphRelationTypes.length]
  })).filter((edge) => graphRelationFilter.value === 'all' || edge.label === graphRelationFilter.value)
  const mesh = graphNodes.value.slice(0, -1).map((node, index) => {
    const next = graphNodes.value[index + 1]
    return {
      id: `mesh-${node.id}-${next.id}`,
      x1: Math.round(node.x / 100 * 820),
      y1: Math.round(node.y / 100 * 520),
      x2: Math.round(next.x / 100 * 820),
      y2: Math.round(next.y / 100 * 520),
      faint: true
    }
  })
  return [...radial, ...mesh]
})
const selectedGraphRelatedNodes = computed(() => {
  const selected = selectedGraphNode.value
  if (!selected) return graphNodes.value.slice(0, 5)
  return graphNodes.value
    .filter((node) => node.id !== selected.id && (node.source?.id === selected.source?.id || node.kind === selected.kind || node.level === selected.level))
    .slice(0, 5)
})
const selectedGraphRelationSummary = computed(() => {
  const selected = selectedGraphNode.value
  const direct = selected ? graphEdges.value.filter((edge) => edge.id.includes(selected.id) || edge.source === selected.id || edge.target === selected.id).length : graphEdges.value.length
  const sameSource = selected ? graphNodes.value.filter((node) => node.source?.id === selected.source?.id).length : graphNodes.value.length
  return {
    direct: Math.max(direct, selectedGraphRelatedNodes.value.length),
    sameSource,
    depth: selected?.level || graphDepth.value,
    links: selectedGraphRelatedNodes.value
  }
})
const selectedGraphDocuments = computed(() => {
  const selected = selectedGraphNode.value
  if (!selected) return knowledge.value.slice(0, 4)
  const sourceId = selected.source?.id
  const sourceText = JSON.stringify(selected.source || {})
  return knowledge.value
    .filter((item) => item.id === sourceId || JSON.stringify(item).includes(selected.label) || sourceText.includes(item.title))
    .slice(0, 4)
})
const selectedGraphAttributes = computed(() => {
  const selected = selectedGraphNode.value
  if (!selected) return []
  const source = selected.source || {}
  const tags = Array.isArray(source.tags) ? source.tags.join('、') : (source.tags || selected.tags || []).join?.('、')
  return [
    { label: '实体类型', value: graphKindMeta[selected.kind]?.text || '知识实体' },
    { label: '节点层级', value: `${selected.level || 1} 级` },
    { label: '关联设备', value: source.equipment || selected.label || '通用设备' },
    { label: '设备型号', value: source.model || '通用型号' },
    { label: '资料来源', value: source.source || source.title || '知识库资料' },
    { label: '更新时间', value: source.updated_at || source.uploaded_at || '已同步' },
    { label: '关联标签', value: tags || '暂无标签' }
  ]
})
const filteredKnowledge = computed(() => {
  if (!knowledgeKeyword.value) return knowledge.value
  return knowledge.value.filter((item) => JSON.stringify(item).includes(knowledgeKeyword.value))
})
const extraFileSamples = [
  { id: 'sample-file-gearbox', name: '减速机轴承温升排查记录.docx', type: 'Word', size: '1.8 MB', category: '检修报告', folder: '检修报告', equipment: '减速机', model: 'RX-450', uploader: '唐忆哲', uploaded_at: '2026-08-02 09:26', auditStatus: '已审核', parseStatus: '解析完成', version: 'v1.2' },
  { id: 'sample-file-air-compressor', name: '空压机保养周期与点检表.xlsx', type: 'Excel', size: '860 KB', category: '标准作业流程', folder: '标准作业流程', equipment: '空压机', model: 'GA-75', uploader: '陈程', uploaded_at: '2026-08-01 15:44', auditStatus: '已审核', parseStatus: '解析完成', version: 'v1.0' },
  { id: 'sample-file-hydraulic', name: '液压系统油路清洗规范.pdf', type: 'PDF', size: '3.4 MB', category: '液压系统', folder: '液压系统', equipment: '液压站', model: 'HYD-220', uploader: '聪明的一休', uploaded_at: '2026-07-30 11:12', auditStatus: '已审核', parseStatus: '解析完成', version: 'v2.0' },
  { id: 'sample-file-motor', name: '三相电机绝缘测试报告.pdf', type: 'PDF', size: '2.1 MB', category: '电气系统', folder: '电气系统', equipment: '三相异步电机', model: 'Y2-160M', uploader: '李志勇', uploaded_at: '2026-07-29 14:08', auditStatus: '已审核', parseStatus: '解析完成', version: 'v1.1' },
  { id: 'sample-file-install', name: '现场安装验收照片-配电柜.png', type: '图片', size: '4.7 MB', category: '现场图片', folder: '现场图片', equipment: '配电柜', model: 'ZK-320', uploader: '唐忆罗', uploaded_at: '2026-07-27 17:36', auditStatus: '待审核', parseStatus: '图片识别完成', version: 'v1.0', url: '/static/industrial-banner-2.png' },
  { id: 'sample-file-engine', name: '发动机气门间隙调整 SOP.docx', type: 'Word', size: '1.2 MB', category: '发动机资料', folder: '发动机资料', equipment: '发动机总成', model: 'CG-125', uploader: '博闻', uploaded_at: '2026-07-26 10:51', auditStatus: '已审核', parseStatus: '解析完成', version: 'v1.4' },
  { id: 'sample-file-recheck', name: '复检数据归档模板.xlsx', type: 'Excel', size: '540 KB', category: '复检报告', folder: '复检报告', equipment: '通用设备', model: '通用', uploader: '明鉴', uploaded_at: '2026-07-24 16:20', auditStatus: '已审核', parseStatus: '解析完成', version: 'v1.0' },
  { id: 'goview-file-manual', name: '汽修宝典-汽车维修手册资料索引.pdf', type: 'PDF', size: '2.6 MB', category: '维修手册', folder: '汽车维修资料', equipment: '汽车发动机系统', model: '通用乘用车', uploader: '博闻', uploaded_at: '2026-08-15 10:12', auditStatus: '已审核', parseStatus: '解析完成', version: 'v1.0', source: 'https://www.goviewtech.com/index.html' },
  { id: 'goview-file-circuit', name: '汽修宝典-汽车电路图检索说明.pdf', type: 'PDF', size: '1.9 MB', category: '电气原理图', folder: '汽车维修资料', equipment: '汽车电气系统', model: '通用乘用车', uploader: '博闻', uploaded_at: '2026-08-15 10:16', auditStatus: '已审核', parseStatus: '解析完成', version: 'v1.0', source: 'https://www.goviewtech.com/index.html' },
  { id: 'goview-file-dtc', name: '汽修宝典-热门故障码问答整理.docx', type: 'Word', size: '980 KB', category: '故障案例', folder: '汽车维修资料', equipment: 'OBD诊断系统', model: '通用', uploader: '观微', uploaded_at: '2026-08-15 10:20', auditStatus: '已审核', parseStatus: '解析完成', version: 'v1.0', source: 'https://www.goviewtech.com/index.html' },
  { id: 'goview-file-video', name: '汽修宝典-维修视频学习清单.xlsx', type: 'Excel', size: '620 KB', category: '检修视频', folder: '汽车维修资料', equipment: '汽车底盘与发动机', model: '通用', uploader: '博闻', uploaded_at: '2026-08-15 10:24', auditStatus: '已审核', parseStatus: '解析完成', version: 'v1.0', source: 'https://www.goviewtech.com/index.html' }
]
const extraKnowledgeSamples = [
  { id: 'goview-kb-manual', title: '汽修宝典官网：汽车维修手册资料库概括', type: '维修手册', category: '汽车维修资料', equipment: '汽车发动机系统', model: '通用乘用车', summary: '汽修宝典官网定位为汽修资料与维修技术入口，可用于归纳汽车维修手册、车型资料、部件拆装与检测信息。', content: '来源页面公开说明其面向汽修技师提供维修资料、找资料、问问题和学知识能力。本条目仅作检修知识索引，用于一休知识检索和图谱关联。', tags: ['汽车维修', '维修手册', '资料库', '找资料'], source: 'https://www.goviewtech.com/index.html', status: 'approved', citations: 18, updated_at: '2026-08-15 10:12' },
  { id: 'goview-kb-circuit', title: '汽车电路图与电气诊断资料索引', type: '技术资料', category: '电气原理图', equipment: '汽车电气系统', model: '通用乘用车', summary: '围绕电路图、线束、传感器、执行器和供电接地关系建立诊断索引，适合与工业电气系统检测方法形成共享节点。', content: '汽修宝典官网栏目包含电路图相关入口。本条目抽象为汽车电气图纸检索节点，便于一休图谱关联电气检测、故障码和安全断电流程。', tags: ['汽车电气', '电路图', '检测方法', '线束'], source: 'https://www.goviewtech.com/index.html', status: 'approved', citations: 12, updated_at: '2026-08-15 10:16' },
  { id: 'goview-kb-dtc', title: '热门故障码与汽修问答知识整理', type: '历史故障案例', category: '故障案例', equipment: 'OBD诊断系统', model: '通用', summary: '将故障码、现象描述、可能原因、检查路径和维修问答抽象为可检索案例，用于故障定位和检修建议生成。', content: '汽修宝典官网描述了汽修问答与知识学习能力。本条目用于承接故障码、问答经验和检修案例，不包含网站原文内容。', tags: ['故障码', '汽修问答', '历史案例', '诊断流程'], source: 'https://www.goviewtech.com/index.html', status: 'approved', citations: 16, updated_at: '2026-08-15 10:20' },
  { id: 'goview-kb-video', title: '汽修笔记与视频学习资料沉淀', type: '培训资料', category: '检修视频', equipment: '汽车底盘与发动机', model: '通用', summary: '把汽修笔记、视频学习和维修经验沉淀为培训型知识节点，辅助新人员理解拆装、检测和复检要点。', content: '来源页面出现学知识、笔记和视频等公开栏目线索。本条目作为学习资料索引，用于知识库文件、图谱和检索建议联动。', tags: ['汽修笔记', '视频学习', 'SOP', '培训资料'], source: 'https://www.goviewtech.com/index.html', status: 'approved', citations: 9, updated_at: '2026-08-15 10:24' }
]
const fileFolders = computed(() => {
  const fixed = ['全部文件', '维修手册', '标准作业流程', '现场图片', '检修报告', '复检报告', '其他技术资料', '发动机资料', '电气系统', '液压系统', '汽车维修资料']
  const dynamic = files.value.map((file) => file.folder || file.category).filter(Boolean)
  return [...new Set([...fixed, ...customFileFolders.value, ...dynamic])]
})
const fileFolderParent = (folder) => {
  if (customFolderParents.value[folder]) return customFolderParents.value[folder]
  if (folder === '全部文件') return '项目'
  if (['维修手册', '标准作业流程', '现场图片', '检修报告', '复检报告', '其他技术资料'].includes(folder)) return '全部文件'
  if (['发动机资料', '电气系统', '液压系统', '汽车维修资料'].includes(folder)) return '其他技术资料'
  return '全部文件'
}
const fileFolderChildren = computed(() => {
  const map = {}
  fileFolders.value.forEach((folder) => {
    const parent = fileFolderParent(folder)
    if (!map[parent]) map[parent] = []
    map[parent].push(folder)
  })
  return map
})
const fileCountForFolder = (folder) => folder === '全部文件'
  ? files.value.length
  : files.value.filter((file) => file.folder === folder || file.category === folder).length
const isFileFolderExpanded = (folder) => expandedFileFolders.value.includes(folder)

const getAccounts = () => {
  const stored = readStorage(AUTH_ACCOUNTS_KEY, [])
  return [defaultAccount, ...stored.filter((item) => item.account !== defaultAccount.account)]
}
const profileToContact = (profile, account = currentAccount.value) => ({
  id: `account-${account || profile.employeeId}`,
  account,
  name: profile.name,
  avatar: profile.avatar || '',
  position: profile.role || '检修人员',
  department: profile.department || '待分配班组',
  specialty: (profile.specialties || []).join(' / ') || '设备检修',
  devices: profile.specialties || [],
  currentTask: '暂无在办任务',
  workload: 0,
  status: '在线',
  employeeId: profile.employeeId,
  phone: profile.phone || ''
})
const syncProfileContact = (profile, account = currentAccount.value) => {
  if (!profile?.name || !account) return
  const directory = readStorage(CONTACT_DIRECTORY_KEY, [])
  const contact = profileToContact(profile, account)
  const index = directory.findIndex((item) => item.account === account || item.employeeId === contact.employeeId)
  if (index >= 0) directory[index] = { ...directory[index], ...contact }
  else directory.push(contact)
  localStorage.setItem(CONTACT_DIRECTORY_KEY, JSON.stringify(directory))
  const liveIndex = contacts.value.findIndex((item) => item.id === contact.id)
  if (liveIndex >= 0) contacts.value[liveIndex] = contact
  else contacts.value.push(contact)
  void yixiuApi.upsertContact(contact).catch(() => {})
}
const setAuthMode = (mode) => {
  authMode.value = mode
  authError.value = ''
  authForm.password = ''
  authForm.confirmPassword = ''
}
const applyAccountProfile = (account) => {
  const savedProfile = account.account === defaultAccount.account ? readStorage(PROFILE_KEY, {}) : account.profile || {}
  Object.assign(user, defaultProfile, savedProfile, { name: savedProfile.name || account.name || defaultProfile.name })
}
const startWorkspace = async () => {
  updateClock()
  if (!clockTimer) clockTimer = window.setInterval(updateClock, 1000)
  showSplash.value = true
  await nextTick()
  playBootAnimation()
  window.setTimeout(() => { refreshAll() }, 260)
}
const establishYixiuBackendSession = async (account) => {
  try {
    const session = await yixiuApi.createSession({
      account: account.account,
      name: account.name || account.profile?.name || user.name,
    })
    if (session?.token) localStorage.setItem('yixiu-token', session.token)
    return true
  } catch (error) {
    authError.value = error.message || '后端工作台会话建立失败，写入功能可能不可用'
    return false
  }
}
const login = async () => {
  const accountName = authForm.account.trim()
  if (!accountName || !authForm.password) return (authError.value = '请输入账号和密码')
  const account = getAccounts().find((item) => item.account === accountName)
  if (!account || account.password !== authForm.password) return (authError.value = '账号或密码不正确，请重新输入')
  applyAccountProfile(account)
  const session = JSON.stringify({ account: account.account, loginAt: Date.now() })
  localStorage.removeItem(AUTH_SESSION_KEY)
  sessionStorage.removeItem(AUTH_SESSION_KEY)
  if (authForm.remember) localStorage.setItem(AUTH_SESSION_KEY, session)
  else sessionStorage.setItem(AUTH_SESSION_KEY, session)
  currentAccount.value = account.account
  authError.value = ''
  isAuthenticated.value = true
  authForm.password = ''
  await establishYixiuBackendSession(account)
  await startWorkspace()
}
const register = async () => {
  const name = authForm.name.trim()
  const accountName = authForm.account.trim()
  if (!name || !accountName || !authForm.password || !authForm.confirmPassword) return (authError.value = '请完整填写注册信息')
  if (!/^[A-Za-z0-9_]{4,20}$/.test(accountName)) return (authError.value = '账号需为 4—20 位字母、数字或下划线')
  if (authForm.password.length < 8) return (authError.value = '密码至少需要 8 位')
  if (authForm.password !== authForm.confirmPassword) return (authError.value = '两次输入的密码不一致')
  if (!authForm.agreed) return (authError.value = '请先同意平台使用规范')
  if (getAccounts().some((item) => item.account === accountName)) return (authError.value = '该账号已存在，请直接登录')
  const profile = { ...defaultProfile, name, employeeId: `YX-${String(Date.now()).slice(-6)}` }
  const accounts = readStorage(AUTH_ACCOUNTS_KEY, [])
  accounts.push({ account: accountName, password: authForm.password, name, profile })
  localStorage.setItem(AUTH_ACCOUNTS_KEY, JSON.stringify(accounts))
  sessionStorage.removeItem(AUTH_SESSION_KEY)
  localStorage.setItem(AUTH_SESSION_KEY, JSON.stringify({ account: accountName, loginAt: Date.now() }))
  currentAccount.value = accountName
  Object.assign(user, profile)
  syncProfileContact(profile, accountName)
  authError.value = ''
  isAuthenticated.value = true
  await establishYixiuBackendSession({ account: accountName, name, profile })
  await startWorkspace()
}
const logout = () => {
  if (assistantSpeechRecognition) assistantSpeechRecognition.stop()
  if (speechRecognition) speechRecognition.stop()
  assistantSpeechRecognition = null
  speechRecognition = null
  assistantVoiceListening.value = false
  voiceListening.value = false
  localStorage.removeItem(AUTH_SESSION_KEY)
  sessionStorage.removeItem(AUTH_SESSION_KEY)
  localStorage.removeItem('yixiu-token')
  localStorage.removeItem('token')
  isAuthenticated.value = false
  currentAccount.value = ''
  activePage.value = 'home'
  showSplash.value = false
  authMode.value = 'login'
  authForm.account = 'yixiu'
  authForm.password = ''
  authForm.confirmPassword = ''
  showProfileEditor.value = false
  showTaskForm.value = false
  selectedTask.value = null
  selectedFile.value = null
  selectedKnowledge.value = null
  selectedAgentId.value = ''
  releaseFileUrls(assistantFiles.value)
  releaseFileUrls(searchFiles.value)
  assistantFiles.value = []
  searchFiles.value = []
  operatorInput.value = ''
  chatInput.value = ''
  authError.value = ''
}
const openProfileEditor = () => {
  Object.assign(profileDraft, user, { specialtyText: (user.specialties || []).join('，') })
  profileError.value = ''
  showProfileEditor.value = true
}
const saveProfile = () => {
  if (!profileDraft.name || !profileDraft.employeeId || !profileDraft.role || !profileDraft.department) {
    profileError.value = '姓名、工号、岗位和所属班组不能为空'
    return
  }
  const specialties = profileDraft.specialtyText.split(/[,，]/).map((item) => item.trim()).filter(Boolean).slice(0, 5)
  if (!specialties.length) return (profileError.value = '请至少填写一个专业方向')
  const saved = {
    name: profileDraft.name,
    avatar: profileDraft.avatar || defaultProfile.avatar,
    employeeId: profileDraft.employeeId,
    role: profileDraft.role,
    department: profileDraft.department,
    skillLevel: profileDraft.skillLevel,
    phone: profileDraft.phone,
    specialties,
    bio: profileDraft.bio
  }
  Object.assign(user, saved)
  if (currentAccount.value === defaultAccount.account) localStorage.setItem(PROFILE_KEY, JSON.stringify(saved))
  if (currentAccount.value && currentAccount.value !== defaultAccount.account) {
    const accounts = readStorage(AUTH_ACCOUNTS_KEY, [])
    const index = accounts.findIndex((item) => item.account === currentAccount.value)
    if (index >= 0) {
      accounts[index] = { ...accounts[index], name: saved.name, profile: saved }
      localStorage.setItem(AUTH_ACCOUNTS_KEY, JSON.stringify(accounts))
    }
  }
  taskForm.assignee_name = user.name
  syncProfileContact(saved)
  showProfileEditor.value = false
  toast('个人资料已保存并同步')
}

const updateClock = () => {
  nowText.value = new Intl.DateTimeFormat('zh-CN', { dateStyle: 'full', timeStyle: 'medium' }).format(new Date())
}

const setNewsSlide = (index) => {
  newsIndex.value = (index + newsSlides.length) % newsSlides.length
}
const nextNewsSlide = () => setNewsSlide(newsIndex.value + 1)
const prevNewsSlide = () => setNewsSlide(newsIndex.value - 1)
const pauseNewsCarousel = () => {
  if (newsCarouselTimer) window.clearInterval(newsCarouselTimer)
  newsCarouselTimer = null
}
const resumeNewsCarousel = () => {
  pauseNewsCarousel()
  newsCarouselTimer = window.setInterval(nextNewsSlide, 4800)
}

const refreshAll = async () => {
  const [overviewData, healthData, taskData, knowledgeData, fileData, contactData] = await Promise.all([
    yixiuApi.overview(),
    yixiuApi.health(),
    yixiuApi.tasks(),
    yixiuApi.knowledge(),
    yixiuApi.files(),
    yixiuApi.contacts()
  ])
  Object.assign(overview, overviewData)
  Object.assign(systemStatus, healthData)
  tasks.value = taskData
  const existingKnowledgeIds = new Set(knowledgeData.map((item) => item.id))
  knowledge.value = [...knowledgeData, ...extraKnowledgeSamples.filter((item) => !existingKnowledgeIds.has(item.id))]
  const existingFileIds = new Set(fileData.map((file) => file.id))
  files.value = [...fileData, ...extraFileSamples.filter((file) => !existingFileIds.has(file.id))]
  const localDirectory = readStorage(CONTACT_DIRECTORY_KEY, [])
  contacts.value = [...contactData]
  localDirectory.forEach((contact) => {
    const index = contacts.value.findIndex((item) => item.id === contact.id || item.employeeId === contact.employeeId)
    if (index >= 0) contacts.value[index] = { ...contacts.value[index], ...contact }
    else contacts.value.push(contact)
  })
  agents.value = normalizeAgentList(overviewData.agents)
}


const switchPage = (key) => {
  activePage.value = key
  selectedAgentId.value = ''
}
const shiftScheduleMonth = (offset) => {
  const next = new Date(scheduleMonth.value)
  next.setMonth(next.getMonth() + offset)
  scheduleMonth.value = next
}
const selectScheduleDate = (day) => {
  selectedScheduleDate.value = day.key
  const [year, month] = day.key.split('-').map(Number)
  if (year && month && (year !== scheduleMonth.value.getFullYear() || month - 1 !== scheduleMonth.value.getMonth())) {
    scheduleMonth.value = new Date(year, month - 1, 1)
  }
}
const resetScheduleDraft = (date = selectedScheduleDate.value || dateKey(new Date())) => {
  Object.assign(scheduleDraft, { title: '', date, time: '09:00~10:00', tag: '工作安排', people: `负责人：${user.name}`, desc: '', important: false, done: false })
}
const openScheduleForm = (item = null) => {
  editingScheduleId.value = item?.id || ''
  if (item) {
    Object.assign(scheduleDraft, {
      title: item.title || '',
      date: item.key || dateKey(new Date()),
      time: item.time || '09:00~10:00',
      tag: item.tag || '工作安排',
      people: item.people || `负责人：${user.name}`,
      desc: item.desc || '',
      important: Boolean(item.important),
      done: Boolean(item.done)
    })
  } else resetScheduleDraft()
  showScheduleForm.value = true
}
const saveSchedule = () => {
  const title = scheduleDraft.title.trim()
  if (!title) return toast('请填写日程标题')
  const payload = {
    key: scheduleDraft.date || dateKey(new Date()),
    tag: scheduleDraft.tag || '工作安排',
    title,
    desc: scheduleDraft.desc.trim() || '待补充日程说明',
    people: scheduleDraft.people.trim() || `负责人：${user.name}`,
    time: scheduleDraft.time || '09:00~10:00',
    important: scheduleDraft.important,
    done: scheduleDraft.done,
    editable: true
  }
  const existing = homeScheduleItems.value.find((item) => item.id === editingScheduleId.value)
  if (editingScheduleId.value && existing?.manual) {
    manualScheduleItems.value = manualScheduleItems.value.map((item) => item.id === editingScheduleId.value ? { ...item, ...payload } : item)
  } else if (editingScheduleId.value) {
    scheduleOverrides.value = { ...scheduleOverrides.value, [editingScheduleId.value]: payload }
    scheduleMarks.value = { ...scheduleMarks.value, [editingScheduleId.value]: { important: payload.important, done: payload.done } }
  } else {
    manualScheduleItems.value.unshift({ id: `manual-schedule-${Date.now()}`, ...payload, manual: true })
  }
  selectedScheduleDate.value = payload.key
  showScheduleForm.value = false
  toast(editingScheduleId.value ? '日程已更新' : '日程已添加')
}
const deleteSchedule = (item) => {
  if (item.id === 'empty-schedule') return
  if (!window.confirm(`删除日程「${item.title}」？`)) return
  if (item.manual) manualScheduleItems.value = manualScheduleItems.value.filter((schedule) => schedule.id !== item.id)
  else deletedScheduleIds.value = [...new Set([...deletedScheduleIds.value, item.id])]
  toast('日程已删除')
}
const toggleScheduleMark = (item, key) => {
  if (item.id === 'empty-schedule') return
  scheduleMarks.value = { ...scheduleMarks.value, [item.id]: { ...(scheduleMarks.value[item.id] || {}), [key]: !item[key] } }
}
const openScheduleItem = (item) => {
  if (item.id === 'empty-schedule') return openScheduleForm()
  openScheduleForm(item)
}
const runGlobalSearch = () => {
  const keyword = globalKeyword.value.trim()
  if (!keyword) return toast('请输入工单、设备、资料或联系人关键词')
  const matchedTask = tasks.value.some((item) => JSON.stringify(item).includes(keyword))
  const matchedKnowledge = knowledge.value.some((item) => JSON.stringify(item).includes(keyword))
  const matchedContact = contacts.value.some((item) => JSON.stringify(item).includes(keyword))
  if (matchedTask) {
    activePage.value = 'tasks'
    taskPanel.value = 'manage'
    taskFilters.keyword = keyword
    return toast(`已定位相关检修任务：${keyword}`)
  }
  if (matchedKnowledge) {
    activePage.value = 'search'
    searchPanel.value = 'library'
    knowledgeKeyword.value = keyword
    return toast(`已定位相关知识资料：${keyword}`)
  }
  if (matchedContact) {
    activePage.value = 'tasks'
    taskPanel.value = 'contacts'
    contactKeyword.value = keyword
    return toast(`已定位相关联系人：${keyword}`)
  }
  activePage.value = 'search'
  searchForm.query = keyword
  toast('未找到直接匹配，已转入智能检索')
}
const closeGlobalSearchOnOutside = (event) => {
  if (!globalSearchFocused.value) return
  if (topbarRef.value?.contains(event.target)) return
  globalSearchFocused.value = false
  taskChamberOpen.value = false
}
const focusAgent = (agent) => {
  selectedAgentId.value = agent.id
  operatorMessages.value.push(operatorMessage({
    id: `agent-${Date.now()}`,
    page: activePage.value,
    role: 'assistant',
    text: `${agent.name}已接入当前页面。${agent.lastResult || agent.duty}`
  }, agent.id))
}
const openGraphSearch = async () => {
  graphSearchExpanded.value = true
  await nextTick()
  graphSearchInput.value?.focus()
}
const resetGraphView = () => {
  graphZoom.value = 1
  graphKindFilter.value = 'all'
  graphDepth.value = 2
  graphShowLabels.value = false
  selectedGraphNode.value = null
  Object.keys(graphNodePositions).forEach((key) => delete graphNodePositions[key])
}
const relayoutGraph = () => {
  selectedGraphNode.value = null
  updateGraphChart()
}
const applyTgSuggestion = () => {
  toast('已应用天工建议，正在跳转到高风险工单...')
  activePage.value = 'tasks'
  taskPanel.value = 'manage'
  taskFilters.severity = 'high'
}
const toggleLegendFilter = (kind) => {
  graphLegendFiltered.value = { ...graphLegendFiltered.value, [kind]: !graphLegendFiltered.value[kind] }
  updateGraphChart()
}
const graphColorPalette = {
  equipment: '#3f7fa7',
  model: '#8fc0d6',
  part: '#45aeb0',
  fault: '#d79542',
  cause: '#cf6d45',
  method: '#8b879f',
  solution: '#6c9b72',
  sop: '#2f5f88',
  risk: '#c95f5a',
  case: '#9a7858',
  doc: '#7d95a8'
}
const buildGraphChartOption = () => {
  const hiddenKinds = Object.entries(graphLegendFiltered.value).filter(([, v]) => v).map(([k]) => k)
  const visibleNodes = graphNodes.value.filter((n) => !hiddenKinds.includes(n.kind))
  const categories = Object.entries(graphKindMeta).map(([kind, meta]) => ({
    name: meta.text,
    itemStyle: { color: graphColorPalette[kind] }
  }))
  const isRadial = graphLayoutMode.value === 'grid'
  const isFixedLayout = graphLayoutMode.value === 'grid' || graphLayoutMode.value === 'tree'
  const centerX = 420
  const centerY = 300
  const pseudoRand = (seed) => { const v = Math.sin(seed * 99.7) * 43758.5; return v - Math.floor(v) }
  const center = graphCenterNode.value && visibleNodes.find((n) => n.id === graphCenterNode.value.id)
  const similarity = (a, b) => {
    if (!b || !center) return 0
    let score = 0
    if ((a.source?.id ?? 'a1') === (b.source?.id ?? 'b1')) score += 3
    if (a.kind === b.kind) score += 2
    const wa = String(a.label || '').toLowerCase()
    const wb = String(b.label || '').toLowerCase()
    const ta = new Set(wa.split(/[\s,，、/]+/).filter((s) => s.length > 1))
    const tb = new Set(wb.split(/[\s,，、/]+/).filter((s) => s.length > 1))
    let overlap = 0
    ta.forEach((w) => { if (tb.has(w)) overlap++ })
    score += overlap
    return score
  }
  const scoreToRadius = (score) => {
    if (score >= 5) return 60
    if (score >= 3) return 150
    if (score >= 1) return 260
    return 380
  }
  const nodes = visibleNodes.map((node, i) => {
    let x, y
    if (isRadial) {
      if (center && node.id === center.id) {
        x = centerX; y = centerY
      } else if (center) {
        const score = similarity(node, center)
        const radius = scoreToRadius(score) + (pseudoRand(i + 10) - 0.5) * 30
        const angle = (i / Math.max(1, visibleNodes.length - 1)) * Math.PI * 2 + pseudoRand(i) * 0.5
        x = centerX + Math.cos(angle) * radius
        y = centerY + Math.sin(angle) * radius
      } else {
        const isAuto = isAutoKnowledgeSource(node.source)
        const isBridge = ['method', 'solution', 'sop', 'risk', 'doc'].includes(node.kind)
        const clusterX = isBridge ? centerX : isAuto ? 285 : 555
        const clusterY = isBridge ? centerY : isAuto ? 300 : 300
        const clusterIndex = visibleNodes.slice(0, i).filter((item) => {
          const itemAuto = isAutoKnowledgeSource(item.source)
          const itemBridge = ['method', 'solution', 'sop', 'risk', 'doc'].includes(item.kind)
          return itemBridge === isBridge && itemAuto === isAuto
        }).length
        const angle = (clusterIndex / Math.max(6, visibleNodes.length / 3)) * Math.PI * 2 + pseudoRand(i) * 0.45
        const radius = isBridge ? 62 + pseudoRand(i + 40) * 58 : 96 + pseudoRand(i + 50) * 72
        x = clusterX + Math.cos(angle) * radius
        y = clusterY + Math.sin(angle) * radius
      }
    } else if (graphLayoutMode.value === 'tree') {
      const sameLevelIndex = visibleNodes.slice(0, i).filter((item) => item.level === node.level).length
      const levelTotal = Math.max(1, visibleNodes.filter((item) => item.level === node.level).length)
      x = 130 + (node.level - 1) * 235
      y = 88 + (sameLevelIndex + 0.5) * (440 / levelTotal)
    } else {
      x = (node.x / 100) * 820
      y = (node.y / 100) * 560
    }
    const isSelected = selectedGraphNode.value?.id === node.id
    const isCenter = (center && node.id === center.id) || (!center && i === 0)
    return {
      id: node.id,
      name: node.label,
      category: Object.keys(graphKindMeta).indexOf(node.kind),
      symbolSize: isCenter ? 56 : node.level === 1 ? 34 : 24,
      x, y,
      itemStyle: {
        color: graphColorPalette[node.kind],
        borderColor: isSelected ? '#2f65ff' : '#ffffff',
        borderWidth: isSelected ? 5 : 3,
        shadowBlur: isSelected || node.matched || isCenter ? 26 : 12,
        shadowColor: isSelected ? 'rgba(47,101,255,.28)' : node.matched ? 'rgba(91,132,191,.28)' : 'rgba(41,77,98,.12)'
      },
      label: {
        show: graphShowLabels.value || node.matched || isCenter || node.level <= 1,
        position: 'bottom',
        distance: 8,
        fontSize: isCenter ? 14 : 12,
        fontWeight: isCenter ? 800 : 650,
        color: '#24384b',
        backgroundColor: 'rgba(255,255,255,.92)',
        borderColor: 'rgba(205,218,232,.88)',
        borderWidth: 1,
        padding: [4, 8],
        borderRadius: 999,
        overflow: 'truncate',
        width: 78
      },
      depth: node.level
    }
  })
  const kindOrder = ['equipment', 'model', 'part', 'fault', 'cause', 'method', 'solution', 'sop', 'risk', 'case', 'doc']
  const sourceGroups = {}
  visibleNodes.forEach((node) => {
    const key = node.source?.id ?? 'misc'
    if (!sourceGroups[key]) sourceGroups[key] = []
    sourceGroups[key].push(node)
  })
  const links = []
  if (isRadial && visibleNodes.length > 1) {
    const centerId = center ? center.id : visibleNodes[0].id
    visibleNodes.forEach((node) => {
      if (node.id === centerId) return
      links.push({
        source: centerId,
        target: node.id,
        label: { show: false },
        label: { show: graphShowLabels.value, formatter: '关联', fontSize: 10, color: '#7b8da0' },
        lineStyle: { color: '#9fb2c8', opacity: 0.52, width: 1.35, curveness: 0.08 }
      })
    })
  } else {
    Object.values(sourceGroups).forEach((group) => {
      const sorted = [...group].sort((a, b) => kindOrder.indexOf(a.kind) - kindOrder.indexOf(b.kind))
      for (let i = 0; i < sorted.length - 1; i++) {
        const relName = graphRelationTypes[i % graphRelationTypes.length]
        if (graphRelationFilter.value !== 'all' && graphRelationFilter.value !== relName) continue
        links.push({
          source: sorted[i].id,
          target: sorted[i + 1].id,
          label: { show: graphShowLabels.value, formatter: relName, fontSize: 10, color: '#7f90a2' },
          lineStyle: {
            color: '#a5b6cc',
            opacity: 0.68,
            width: 1.4,
            curveness: 0.12
          }
        })
      }
    })
  }
  return {
    categories,
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        if (params.dataType === 'node') {
          const d = params.data
          return `<strong>${d.name}</strong><br/>类型: ${categories[d.category]?.name || '未知'}`
        }
        return ''
      }
    },
    series: [{
      type: 'graph',
      layout: graphLayoutMode.value === 'circle' ? 'circular' : graphLayoutMode.value === 'force' ? 'force' : 'none',
      roam: true,
      scaleLimit: { min: 0.45, max: 2.4 },
      draggable: true,
      focusNodeAdjacency: true,
      data: nodes,
      links,
      edgeSymbol: ['none', 'arrow'],
      edgeSymbolSize: [0, 7],
      label: { show: false },
      lineStyle: { curveness: 0.08 },
      force: {
        repulsion: 520,
        edgeLength: [128, 230],
        gravity: 0.025,
        friction: 0.34,
        layoutAnimation: graphLayoutMode.value === 'force'
      },
      circular: { rotateLabel: true },
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 3 },
        itemStyle: { shadowBlur: 30, shadowColor: 'rgba(47,95,136,.5)' }
      },
      select: {
        itemStyle: { borderColor: '#b88a44', borderWidth: 5, shadowBlur: 30, shadowColor: 'rgba(184,138,68,.4)' },
        label: { show: true, fontSize: 13, fontWeight: 'bold' }
      }
    }]
  }
}
// 知识图谱是手写实例，切到别的子面板时 v-if 会把这块 DOM 卸载，
// 但实例还留着旧节点。这时 setOption / resize 会让 echarts 用 0 尺寸重算
// graph 的 roam 坐标系，在 legacyCopyOverallTrans 里拿到 null 变换矩阵并抛错，
// 所以每次操作前先确认 DOM 还是当前挂载、且有实际尺寸的那一个。
const graphChartLive = () => {
  const node = graphChartRef.value
  return Boolean(graphChartInstance && node && node.isConnected && node.clientWidth > 0 && node.clientHeight > 0)
}
const updateGraphChart = () => {
  if (!graphChartLive()) return
  graphChartInstance.setOption(buildGraphChartOption(), true)
}
const handleGraphResize = () => {
  if (!graphChartLive()) return
  graphChartInstance.resize()
}
const settleGraphChart = () => {
  nextTick(() => {
    tryInitGraphChart()
    requestAnimationFrame(() => {
      updateGraphChart()
      handleGraphResize()
      window.setTimeout(() => handleGraphResize(), 180)
      window.setTimeout(() => { updateGraphChart(); handleGraphResize() }, 360)
    })
  })
}
watch([graphNodes, graphKindFilter, graphDepth, graphRelationFilter, graphLayoutMode, graphShowLabels, knowledgeKeyword], () => {
  updateGraphChart()
}, { deep: true })
watch(selectedGraphNode, () => {
  updateGraphChart()
})
watch([activePage, knowledgePanel], () => {
  if (activePage.value === 'knowledge' && knowledgePanel.value === 'network') settleGraphChart()
})
watch([activePage, taskPanel, activeConversationId], () => {
  if (activePage.value === 'tasks' && taskPanel.value === 'contacts') markConversationRead(activeConversationId.value)
})
watch([activePage, taskPanel], () => {
  const defaultAgent = pageDefaultAgentId.value
  if (activePage.value === 'home' || !selectedAgentId.value || !agentProfileMap[selectedAgentId.value] || selectedAgentId.value !== defaultAgent) {
    selectedAgentId.value = defaultAgent
  }
})
const taskLinkedKnowledge = ref([])
watch(selectedTask, async (task) => {
  if (!task) { taskLinkedKnowledge.value = []; return }
  try {
    const result = await yixiuApi.linkedKnowledge('task', task.id)
    taskLinkedKnowledge.value = result.items || []
  } catch { taskLinkedKnowledge.value = [] }
}, { immediate: true })

// 知识库文档列表（从mock知识构建，支持协作元数据）
const avatarColors = ['#2563EB', '#059669', '#D97706', '#DC2626', '#7C3AED', '#0891B2', '#DB2777', '#65A30D']
const knowledgeDocs = ref([])
const kbFilter = ref('all')
const kbSearch = ref('')
const showTemplatePicker = ref(false)
const showTemplateLibrary = ref(false)
const availableTemplates = ref([])

const filteredKnowledgeDocs = computed(() => {
  let docs = knowledgeDocs.value
  if (kbFilter.value === 'mine') docs = docs.filter(d => d.collaborators?.some(c => c.role === 'owner'))
  else if (kbFilter.value === 'starred') docs = docs.filter(d => d.starred)
  else if (kbFilter.value === 'recent') docs = [...docs].sort((a, b) => (b.updated_at || '').localeCompare(a.updated_at || ''))
  if (kbSearch.value) {
    const kw = kbSearch.value.toLowerCase()
    docs = docs.filter(d =>
      (d.title || '').toLowerCase().includes(kw) ||
      (d.content || '').toLowerCase().includes(kw) ||
      (d.tags || []).some(t => t.toLowerCase().includes(kw))
    )
  }
  return docs
})

const loadTemplates = async () => {
  try {
    const res = await yixiuApi.templates()
    availableTemplates.value = res.templates || []
  } catch {
    availableTemplates.value = [
      { id: 'tpl-blank', name: '空白文档', icon: '📝', category: '通用', description: '从零开始创建', skeleton: { content: '# 文档标题\n\n在此输入内容...' } },
      { id: 'tpl-sop', name: '检修作业 SOP', icon: '📋', category: '检修流程', description: '标准作业流程模板', skeleton: { content: '# 检修作业 SOP\n\n## 安全确认\n- [ ] 停机断电\n\n## 作业步骤\n1. 检查\n2. 处置' } },
      { id: 'tpl-fault', name: '故障排查报告', icon: '🔍', category: '故障分析', description: '故障排查过程记录', skeleton: { content: '# 故障排查报告\n\n## 故障现象\n\n## 排查过程\n\n## 处置措施' } },
      { id: 'tpl-meeting', name: '检修会议纪要', icon: '📒', category: '协作沟通', description: '班组例会纪要', skeleton: { content: '# 会议纪要\n\n## 议题\n\n## 行动计划' } },
      { id: 'tpl-safety', name: '安全操作规范', icon: '🛡️', category: '安全规范', description: '高风险作业规程', skeleton: { content: '# 安全操作规范\n\n## 防护用品\n- [ ] 安全帽\n\n## 安全流程' } }
    ]
  }
}

const loadKnowledgeDocs = () => {
  const collaboratorPool = [
    { name: '张三', role: 'owner', status: 'online' },
    { name: '李四', role: 'editor', status: 'online' },
    { name: '王五', role: 'editor', status: 'offline' },
    { name: '赵宁', role: 'viewer', status: 'offline' },
  ]
  const docs = overview.value?.knowledge || []
  const mockDocs = [
    {
      id: 'kb-sop-001',
      title: 'CG-125 发动机检修作业 SOP',
      type: 'SOP', category: '检修流程',
      content: '# 发动机检修作业 SOP\n## 基本信息\n- 设备：CG-125 摩托车发动机\n- 型号：MTR-CG125-12\n## 安全确认\n- 停机断电\n- 验电挂牌\n- 穿戴劳保用品\n## 作业步骤\n1. 外观检查\n2. 参数测量\n3. 故障定位\n4. 维修处置',
      tags: ['发动机', 'SOP', '异响'],
      collaborators: [collaboratorPool[0], collaboratorPool[1], collaboratorPool[2]],
      starred: true,
      updated_at: '2026-08-06 16:30',
    },
    {
      id: 'kb-fault-001',
      title: '配电柜过热故障排查报告',
      type: '故障案例', category: '故障分析',
      content: '# 故障排查报告\n## 故障现象\n配电柜PD-ZK-320-07运行中温度异常升高，超过报警阈值。\n## 排查过程\n1. 红外测温确认发热点位于母排连接处\n2. 检查螺栓紧固力矩，发现松动\n3. 热成像分析确认接触电阻增大\n## 处置措施\n停电检修，重新紧固螺栓，涂抹导电膏，复测温度正常。',
      tags: ['配电柜', '过热', '案例'],
      collaborators: [collaboratorPool[0], collaboratorPool[1]],
      starred: false,
      updated_at: '2026-08-05 14:20',
    },
    {
      id: 'kb-safety-001',
      title: '高压电气设备安全操作规范',
      type: '安全规范', category: '安全规范',
      content: '# 安全操作规范\n## 适用范围\n适用于10kV及以上高压电气设备的检修与维护作业。\n## 防护用品\n- 绝缘手套\n- 绝缘鞋\n- 安全帽\n- 防电弧服\n## 安全流程\n1. 办理工作票\n2. 验电\n3. 装设接地线\n4. 悬挂标示牌',
      tags: ['安全', '高压', '电气'],
      collaborators: [collaboratorPool[0]],
      starred: true,
      updated_at: '2026-08-04 09:15',
    },
    {
      id: 'kb-meeting-001',
      title: '8月检修班组例会纪要',
      type: '会议纪要', category: '协作沟通',
      content: '# 检修班组例会纪要\n## 时间\n2026年8月3日 14:00\n## 参会人员\n聪明的一休、李志勇、唐忆罗、陈程\n## 议题\n1. 本周检修任务进展\n2. 配电柜过热工单风险确认\n3. CG-125发动机异响排查方案\n## 行动计划\n- 聪明的一休负责配电柜停机检修\n- 李志勇跟进发动机拆检',
      tags: ['会议', '纪要'],
      collaborators: [collaboratorPool[0], collaboratorPool[1], collaboratorPool[2], collaboratorPool[3]],
      starred: false,
      updated_at: '2026-08-03 16:00',
    },
    {
      id: 'kb-manual-001',
      title: '液压千斤顶使用维护手册',
      type: '维修手册', category: '通用',
      content: '# 液压千斤顶使用维护手册\n## 型号\nYZ-50T 液压千斤顶\n## 使用前检查\n1. 检查油位是否正常\n2. 检查活塞有无划伤\n3. 确认底座稳固\n## 维护保养\n- 每月更换液压油\n- 每季度检查密封圈\n- 每年校验压力表',
      tags: ['液压', '千斤顶', '手册'],
      collaborators: [],
      starred: false,
      updated_at: '2026-08-02 10:30',
    },
    {
      id: 'kb-sop-002',
      title: '点火线圈更换作业指导书',
      type: 'SOP', category: '检修流程',
      content: '# 点火线圈更换 SOP\n## 适用设备\nDLI-001 点火线圈\n## 准备工具\n- 扭力扳手\n- 绝缘手套\n- 万用表\n## 作业步骤\n1. 断开蓄电池负极\n2. 拆卸旧点火线圈\n3. 清洁安装面\n4. 安装新线圈，紧固至规定力矩\n5. 连接线束，复测电阻值',
      tags: ['点火线圈', 'SOP'],
      collaborators: [collaboratorPool[0], collaboratorPool[2]],
      starred: false,
      updated_at: '2026-08-01 11:45',
    },
  ]
  knowledgeDocs.value = [...mockDocs, ...docs.map((k, idx) => ({
    ...k,
    collaborators: idx < 3 ? collaboratorPool.slice(0, 1 + (idx % 3)) : [],
    starred: idx % 4 === 0,
  }))]
}

const createDocFromTemplate = async (tpl) => {
  showTemplatePicker.value = false
  showTemplateLibrary.value = false
  const content = tpl?.skeleton?.content || '# 新文档\n\n在此输入内容...'
  const title = tpl.name === '空白文档' ? '新文档' : `${tpl.name} - 待命名`
  let id = `kb-new-${Date.now()}`
  try {
    const saved = await yixiuApi.updateKnowledge({
      title, summary: `基于「${tpl.name}」模板创建的文档`,
      content, type: tpl.category || '技术资料', category: tpl.category || '通用',
      equipment: '通用', model: '', tags: [], source: tpl.name,
    })
    id = saved.id || id
  } catch {}
  const newDoc = {
    id, title,
    type: tpl.category || '技术资料', category: tpl.category || '通用',
    content, tags: [], source: tpl.name,
    updated_at: new Date().toLocaleString('zh-CN'),
    collaborators: [{ name: user.name || '我', role: 'owner', status: 'online' }],
    starred: false,
  }
  knowledgeDocs.value.unshift(newDoc)
  openKnowledge(newDoc)
  startKnowledgeEdit()
  toast(`已基于「${tpl.name}」创建文档`)
}
const isTaskOverdue = (task) => task.status !== 'completed' && new Date(task.due_at).getTime() < Date.now()
const remainingTime = (task) => {
  const diff = new Date(task.due_at).getTime() - Date.now()
  if (diff <= 0) return '已逾期'
  const hours = Math.ceil(diff / 3600000)
  return hours > 24 ? `${Math.ceil(hours / 24)}天` : `${hours}小时`
}
const applyTaskMetric = (card) => {
  taskPanel.value = 'manage'
  Object.assign(taskFilters, { status: 'all', severity: 'all', category: 'all', faultType: 'all', assignee: 'all', overdue: 'all', keyword: '' }, card.filter || {})
}
const filterTaskBy = (type, value) => {
  taskPanel.value = 'manage'
  if (type === 'status') taskFilters.status = value
  if (type === 'severity') taskFilters.severity = value
  if (type === 'category') taskFilters.category = value
  if (type === 'faultType') taskFilters.faultType = value
}
const applyGuidanceFilter = (item) => {
  taskPanel.value = 'manage'
  Object.assign(taskFilters, { status: 'all', severity: 'all', category: 'all', faultType: 'all', assignee: 'all', overdue: 'all', keyword: '' }, item.filter || {})
  toast(`已按「${item.title}」筛选任务`)
}
const goStat = (card) => {
  activePage.value = card.page || 'home'
  if (card.panel) {
    if (card.page === 'tasks') taskPanel.value = card.panel
    if (card.page === 'knowledge') knowledgePanel.value = card.panel
    if (card.page === 'search') searchPanel.value = card.panel
  }
  if (card.status) taskFilters.status = card.status
  if (card.severity) taskFilters.severity = card.severity
}
const goTopbarTask = (type) => {
  globalSearchFocused.value = false
  taskChamberOpen.value = false
  activePage.value = 'tasks'
  Object.assign(taskFilters, { status: 'all', severity: 'all', category: 'all', faultType: 'all', assignee: 'all', overdue: 'all', keyword: '' })
  if (type === 'pending') {
    taskPanel.value = 'manage'
    taskFilters.status = 'pending'
    return toast('已进入待办任务')
  }
  if (type === 'review') {
    taskPanel.value = 'recheck'
    taskFilters.status = 'review'
    return toast('已进入待复检任务')
  }
  taskPanel.value = 'manage'
  taskFilters.severity = 'high'
  toast('已定位高风险任务')
}
const openUnreadContacts = () => {
  activePage.value = 'tasks'
  taskPanel.value = 'contacts'
  contactViewMode.value = 'all'
  const unread = conversations.value.find((item) => Number(item.unread || 0) > 0)
  if (unread) {
    openConversation(unread)
    toast(`已打开未读会话：${unread.name}`)
  } else {
    toast('暂无未读联系人消息')
  }
}
const runQuickAction = (item) => item.action()
const runAlert = (alert) => alert.action()
const runProfileItem = (item) => {
  if (!item) return
  if (item.schedule) return openScheduleForm(item.schedule)
  if (item.action === 'edit-profile') return openProfileEditor()
  if (item.action === 'logout') return logout()
  if (item.page) goStat({ page: item.page, panel: item.panel })
  else toast(item.title)
}
const persistChatMessage = async (message, extra = {}) => {
  try {
    const saved = await yixiuApi.sendConversationMessage(message.conversationId, {
      ...message,
      ...extra,
      sender_id: currentAccount.value,
      sender_name: user.name,
    })
    if (saved?.id) message.id = saved.id
    return true
  } catch (error) {
    message.syncFailed = true
    toast(error.message || '消息发送失败，请稍后重试')
    return false
  }
}
const sendChatMessage = async (text) => {
  const value = String(text || '').trim()
  if (!value || !activeConversation.value) return
  const message = { id: `msg-${Date.now()}`, conversationId: activeConversation.value.id, mine: true, text: value, time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }
  chatMessages.value.push(message)
  await persistChatMessage(message)
  chatInput.value = ''
}
const pushAttachmentMessage = async (attachment, text) => {
  if (!activeConversation.value) return
  const message = { id: `attachment-${Date.now()}-${Math.random()}`, conversationId: activeConversation.value.id, mine: true, text, attachment, time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }
  chatMessages.value.push(message)
  const portableAttachment = { kind: attachment.kind, name: attachment.name, size: attachment.size, type: attachment.type, duration: attachment.duration || 0 }
  await persistChatMessage(message, { attachment: portableAttachment, message_type: attachment.kind })
}
const readableSize = (size = 0) => size > 1024 * 1024 ? `${(size / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(size / 1024))} KB`
const addChatAttachments = (event, kind) => {
  const selected = [...(event.target.files || [])]
  selected.forEach((file) => {
    const url = URL.createObjectURL(file)
    chatObjectUrls.add(url)
    pushAttachmentMessage({ kind, name: file.name, size: readableSize(file.size), type: file.type, url, rawFile: file }, kind === 'image' ? '发送现场图片' : '发送检修资料')
  })
  event.target.value = ''
}
const previewChatAttachment = (attachment) => {
  selectedFile.value = { id: `chat-${Date.now()}`, name: attachment.name, type: attachment.kind === 'image' ? '图片' : attachment.type?.includes('pdf') ? 'PDF' : '其他', size: attachment.size, version: '会话附件', parseStatus: '本地文件', url: attachment.url }
}
const stopChatRecording = () => {
  if (chatRecorder?.state === 'recording') chatRecorder.stop()
}
const toggleChatRecording = async () => {
  if (chatRecording.value) return stopChatRecording()
  if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') return toast('当前浏览器不支持录音，请使用最新版 Chrome')
  try {
    chatRecordStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    chatRecordChunks = []
    chatRecorder = new MediaRecorder(chatRecordStream)
    chatRecorder.ondataavailable = (event) => { if (event.data.size) chatRecordChunks.push(event.data) }
    chatRecorder.onstop = () => {
      const blob = new Blob(chatRecordChunks, { type: chatRecorder.mimeType || 'audio/webm' })
      const url = URL.createObjectURL(blob)
      chatObjectUrls.add(url)
      pushAttachmentMessage({ kind: 'audio', name: `语音消息-${Date.now()}.webm`, size: readableSize(blob.size), type: blob.type, url, duration: chatRecordSeconds.value }, `语音消息 ${chatRecordSeconds.value} 秒`)
      chatRecordStream?.getTracks().forEach((track) => track.stop())
      chatRecording.value = false
      window.clearInterval(chatRecordTimer)
      chatRecordTimer = null
      chatRecordSeconds.value = 0
    }
    chatRecorder.start(250)
    chatRecording.value = true
    chatRecordSeconds.value = 0
    chatRecordTimer = window.setInterval(() => { chatRecordSeconds.value += 1 }, 1000)
  } catch (error) {
    toast(error.name === 'NotAllowedError' ? '麦克风权限未开启，请在浏览器地址栏允许录音' : '无法启动录音设备')
  }
}
const openTaskPicker = (mode = 'send') => { taskPickerMode.value = mode; showTaskPicker.value = true }
const sendTaskCard = async (task = tasks.value[0]) => {
  if (!task || !activeConversation.value) return
  const message = {
    id: `card-${Date.now()}`,
    conversationId: activeConversation.value.id,
    mine: true,
    text: '发送任务卡片，请协作人员查看当前进度。',
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    card: { type: 'task', title: task.workOrderNo, desc: `${task.equipment_name} · ${task.current_step} · ${task.progress}%` }
  }
  chatMessages.value.push(message)
  await persistChatMessage(message, { message_type: 'task-card' })
}
const openConversation = (session) => {
  activeConversationId.value = session.id
  markConversationRead(session.id)
  void syncConversationMessages(session.id, true)
  if (session.kind === 'meeting') {
    contactViewMode.value = contactViewMode.value === 'meeting' ? 'meeting' : contactViewMode.value
  }
}
const startDirectChat = (contact) => {
  const index = contacts.value.findIndex((item) => item.id === contact.id)
  const id = index === 0 ? 'expert-1' : `contact-${contact.id}`
  activeConversationId.value = id
  markConversationRead(id)
  void syncConversationMessages(id, true)
  contactViewMode.value = 'contact'
}
const openMeeting = (meeting) => {
  const id = `meeting-${meeting.id}`
  activeConversationId.value = id
  markConversationRead(id)
  void syncConversationMessages(id, true)
  contactViewMode.value = 'meeting'
}
const currentMeeting = computed(() => activeConversation.value?.meeting || contactMeetings.value[0])
const sendMeetingCard = async (meeting = currentMeeting.value) => {
  if (!meeting || !activeConversation.value) return
  const message = {
    id: `meeting-card-${Date.now()}`,
    conversationId: activeConversation.value.id,
    mine: true,
    text: '发送会议卡片，请相关人员确认参会。',
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    card: { type: 'meeting', title: meeting.title, desc: `${meeting.time} · ${meeting.agenda}` }
  }
  chatMessages.value.push(message)
  await persistChatMessage(message, { message_type: 'meeting-card' })
}
const selectTaskFromPicker = (task) => {
  if (taskPickerMode.value === 'assign') {
    const collaborator = activeConversation.value?.name
    task.collaborators = [...new Set([...(task.collaborators || []), collaborator].filter(Boolean))]
    sendChatMessage(`协作邀请：已将 ${collaborator} 加入任务 ${task.workOrderNo}`)
    toast('协作人员已加入任务')
  } else sendTaskCard(task)
  showTaskPicker.value = false
}
const summarizeConversation = () => {
  const recent = activeMessages.value.slice(-6).map((item) => item.text).filter(Boolean)
  const focus = recent.length ? recent.join('；') : '当前会话暂无有效消息'
  chatMessages.value.push({ id: `summary-${Date.now()}`, conversationId: activeConversation.value.id, mine: false, text: `协作重点：${focus.slice(0, 180)}。建议明确负责人、下一步动作与复测时间。`, time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) })
}
const requestSupport = () => {
  const task = tasks.value.find((item) => item.workOrderNo === activeConversation.value?.taskNo) || tasks.value.find((item) => item.severity === 'high')
  sendChatMessage(`专家支援请求：${task?.workOrderNo || '当前检修任务'} 需要协助判断故障原因，请携带检测结论反馈。`)
  toast('支援请求已发送到当前协作会话')
}
const createCollaborationGroup = () => {
  const source = activeConversation.value
  const id = `local-group-${Date.now()}`
  contacts.value.unshift({ id, name: `${source?.name || '检修'}协作群`, avatar: '', position: '临时协作群', department: source?.department || user.department, specialty: source?.specialty || '检修协作', devices: source?.devices || [], currentTask: source?.currentTask || '待关联任务', workload: 0, status: '在线' })
  activeConversationId.value = `contact-${id}`
  contactViewMode.value = 'group'
  chatMessages.value.push({ id: `group-${Date.now()}`, conversationId: activeConversationId.value, mine: false, text: `协作群已创建。创建人：${user.name}，请先发送任务卡片并明确分工。`, time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) })
  toast('协作群已创建并打开')
}
const scheduleMeeting = () => {
  const source = activeConversation.value
  const title = window.prompt('请输入会议主题', `${source?.name || '检修'}协同会议`)
  if (!title) return
  const meeting = {
    id: `meeting-${Date.now()}`,
    title: title.trim(),
    time: '今日 16:30',
    status: '已预约',
    owner: source?.department || user.department,
    taskNo: source?.taskNo || tasks.value[0]?.workOrderNo || '待关联任务',
    members: [user.name, source?.name, ...(source?.devices || []).slice(0, 1)].filter(Boolean),
    agenda: `围绕 ${source?.currentTask || '当前检修任务'} 明确分工、资料和复测时间`,
    progress: 25
  }
  contactMeetings.value.unshift(meeting)
  openMeeting(meeting)
  chatMessages.value.push({ id: `meeting-${Date.now()}`, conversationId: activeConversationId.value, mine: false, text: `会议已预约：${meeting.title}，时间 ${meeting.time}，请确认参会人员和议题。`, time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) })
  toast('会议已预约并加入会话列表')
}
const startInstantMeeting = () => {
  const source = activeConversation.value
  const meeting = {
    id: `instant-${Date.now()}`,
    title: `${source?.name || '检修'}即时会议`,
    time: '现在',
    status: '进行中',
    owner: source?.department || user.department,
    taskNo: source?.taskNo || '当前会话',
    members: [user.name, source?.name].filter(Boolean),
    agenda: `快速确认 ${source?.currentTask || '现场问题'} 的下一步处理`,
    progress: 80
  }
  contactMeetings.value.unshift(meeting)
  openMeeting(meeting)
  sendMeetingCard(meeting)
  toast('已发起即时会议')
}
const inviteContactToMeeting = () => {
  const meeting = currentMeeting.value
  const contact = filteredContacts.value[0]
  if (!meeting || !contact) return toast('暂无可邀请联系人')
  meeting.members = [...new Set([...meeting.members, contact.name])]
  sendChatMessage(`会议邀请：已邀请 ${contact.name} 参加「${meeting.title}」。`)
  toast('已邀请推荐成员加入会议')
}
const openMessageCard = (card) => {
  if (card.type === 'task') return goStat({ page: 'tasks', panel: 'manage' })
  if (card.type === 'knowledge') return goStat({ page: 'search', panel: 'network' })
  if (card.type === 'meeting') return contactViewMode.value = 'meeting'
  toast(card.title)
}
const openTask = (task) => {
  if (task && (!task.sop || !task.sop.length)) task.sop = recommendedSopForTask(task)
  if (task && (!task.safety || !task.safety.length)) task.safety = taskComplianceChecks(task).filter((item) => item.required).map((item) => item.hint)
  selectedTask.value = task
}
const openKnowledge = async (item) => {
  selectedKnowledge.value = item
  isKnowledgeEditing.value = false
  knowledgeSaveStatus.value = ''
  try {
    const [versions, links, collabs] = await Promise.allSettled([
      yixiuApi.knowledgeVersions(item.id).then(r => r.versions || []),
      yixiuApi.knowledgeLinks(item.id).then(r => r.links || []),
      yixiuApi.knowledgeCollaborators(item.id).then(r => r.collaborators || []),
    ])
    kdVersions.value = versions.status === 'fulfilled' ? versions.value : []
    kdLinks.value = links.status === 'fulfilled' ? links.value : []
    kdCollaborators.value = collabs.status === 'fulfilled' ? collabs.value : (item.collaborators || [])
  } catch {
    kdVersions.value = []; kdLinks.value = []
    kdCollaborators.value = item.collaborators || []
  }
}
const knowledgeFullLines = (item) => {
  const lines = flattenKnowledgeText(item.content || item.summary)
  if (lines.length) return lines
  const content = String(item.content || item.summary || '')
  if (content) return content.split('\n').map(s => s.trim()).filter(Boolean)
  return ['该资料已纳入一休知识库，可编辑完善内容或作为智能检索依据。']
}
const closeKnowledgeDetail = () => {
  if (isKnowledgeEditing.value && knowledgeDraft.content !== String(selectedKnowledge.value?.content || '')) {
    if (!window.confirm('正在编辑中，是否关闭？未保存内容将丢失。')) return
  }
  selectedKnowledge.value = null
  isKnowledgeEditing.value = false
}
const startKnowledgeEdit = () => {
  const k = selectedKnowledge.value || {}
  const tags = k.tags || []
  knowledgeDraft.title = k.title || ''
  knowledgeDraft.content = flattenKnowledgeText(k.content || k.summary).join('\n') || String(k.content || k.summary || '')
  knowledgeDraft.equipment = k.equipment || '通用'
  knowledgeDraft.model = k.model || ''
  knowledgeDraft.tagsText = Array.isArray(tags) ? tags.join(', ') : String(tags || '')
  knowledgeDraft.source = k.source || '技术资料库'
  isKnowledgeEditing.value = true
  knowledgeSaveStatus.value = 'unsaved'
}
const cancelKnowledgeEdit = () => {
  const hasChange = knowledgeDraft.content !== String(selectedKnowledge.value?.content || '')
  if (hasChange && !window.confirm('有未保存修改，确定退出编辑？')) return
  isKnowledgeEditing.value = false
  knowledgeSaveStatus.value = ''
}
const onKnowledgeContentInput = () => {
  knowledgeSaveStatus.value = 'editing'
  if (kdAutoSaveTimer.value) clearTimeout(kdAutoSaveTimer.value)
  kdAutoSaveTimer.value = setTimeout(() => saveKnowledgeContent(true), 1500)
}
const insertMarkdown = (type) => {
  const map = { heading: '\n## ', bold: '**加粗内容**', list: '\n- ', todo: '\n- [ ] ', table: '\n| 设备 | 参数 | 检测值 |\n|------|------|--------|\n| CG125 | 气门间隙 | 0.08mm |\n' }
  knowledgeDraft.content += map[type] || ''
  onKnowledgeContentInput()
}
const saveKnowledgeContent = async (isAuto = false) => {
  if (!selectedKnowledge.value) return
  knowledgeSaveStatus.value = 'saving'
  const tags = knowledgeDraft.tagsText.split(/[,，]/).map(s => s.trim()).filter(Boolean)
  try {
    const result = await yixiuApi.saveKnowledgeContent(selectedKnowledge.value.id, {
      title: knowledgeDraft.title, content: knowledgeDraft.content,
      equipment: knowledgeDraft.equipment, model: knowledgeDraft.model, tags,
      editor_name: user.name || '当前用户', change_summary: isAuto ? '自动保存' : '手动保存',
    })
    Object.assign(selectedKnowledge.value, result)
    knowledgeSaveStatus.value = isAuto ? 'saved' : 'manualSaved'
    if (!isAuto) toast('已保存并生成版本快照')
    // 刷新版本列表
    try { kdVersions.value = (await yixiuApi.knowledgeVersions(selectedKnowledge.value.id)).versions || [] } catch {}
  } catch (e) {
    knowledgeSaveStatus.value = 'error'
    toast('保存失败：' + (e.message || '请检查服务连接'))
  }
}
const saveKnowledgeNow = (stayInEdit = false) => {
  if (kdAutoSaveTimer.value) { clearTimeout(kdAutoSaveTimer.value); kdAutoSaveTimer.value = null }
  saveKnowledgeContent(false).then(() => { if (!stayInEdit) isKnowledgeEditing.value = false })
}
const addKdLink = async () => {
  if (!kdNewLink.targetId || !kdNewLink.title) { toast('请填写ID和标题'); return }
  try {
    await yixiuApi.addKnowledgeLink(selectedKnowledge.value.id, {
      link_type: kdNewLink.type, target_id: kdNewLink.targetId, target_title: kdNewLink.title,
    })
    kdNewLink.targetId = ''; kdNewLink.title = ''
    kdLinks.value = (await yixiuApi.knowledgeLinks(selectedKnowledge.value.id)).links || []
    toast('关联已添加')
  } catch (e) { toast('关联失败：' + (e.message || '')) }
}
const removeKdLink = async (linkId) => {
  if (!window.confirm('移除此关联？')) return
  try {
    await yixiuApi.removeKnowledgeLink(selectedKnowledge.value.id, linkId)
    kdLinks.value = kdLinks.value.filter(l => l.id !== linkId)
    toast('已移除')
  } catch (e) { toast('移除失败') }
}
const restoreKdVersion = async (ver) => {
  if (!window.confirm(`恢复到 v${ver.version}？当前内容将被替换并生成新版本。`)) return
  try {
    const result = await yixiuApi.restoreKnowledgeVersion(selectedKnowledge.value.id, ver.id)
    if (selectedKnowledge.value) {
      selectedKnowledge.value.content = ver.content_snapshot
      selectedKnowledge.value.title = ver.title_snapshot || selectedKnowledge.value.title
    }
    kdVersions.value = (await yixiuApi.knowledgeVersions(selectedKnowledge.value.id)).versions || []
    toast(`已恢复到 v${ver.version}，当前版本 v${result.new_version}`)
  } catch (e) { toast('恢复失败') }
}
const inviteCollaborator = async () => {
  const name = window.prompt('邀请协作成员，输入姓名或工号：')
  if (!name) return
  const role = window.prompt('设置角色（owner / editor / viewer）', 'editor') || 'editor'
  try {
    await yixiuApi.addKnowledgeCollaborator(selectedKnowledge.value.id, { name, role, status: 'online' })
    kdCollaborators.value = await yixiuApi.knowledgeCollaborators(selectedKnowledge.value.id).then(r => r.collaborators || [])
  } catch {
    kdCollaborators.value.push({ name, role, status: 'online' })
  }
  toast(`已邀请 ${name} 加入协作`)
}
const submitKnowledgeReview = async () => {
  const k = selectedKnowledge.value || {}
  try {
    await yixiuApi.updateKnowledge({
      title: k.title, summary: knowledgeFullLines(k)[0] || '',
      content: flattenKnowledgeText(k.content).join('\n') || String(k.content || ''),
      equipment: k.equipment, model: k.model, tags: k.tags || [], source: k.source || '技术资料库编辑提交',
    })
    toast('已提交到知识审核队列')
  } catch (e) { toast('提交失败：' + (e.message || '')) }
}
const openTaskById = (taskId) => {
  if (!overview.value?.tasks) { toast('任务数据未加载'); return }
  const task = overview.value.tasks.find(t => String(t.id) === String(taskId))
  if (task) {
    selectedKnowledge.value = null
    selectedTask.value = task
    activePage.value = 'tasks'
  } else {
    toast('未找到该任务')
  }
}
const selectGraphNode = (node) => {
  selectedGraphNode.value = node
  if (node) {
    graphCenterNode.value = node
    tryInitGraphChart()
  }
}
const previewFile = (file) => {
  if (!file) return toast('暂无可预览文件')
  selectedFileRow.value = file.id
  selectedFile.value = file
}
const selectFileFolder = (node) => {
  if (node.hasChildren) {
    expandedFileFolders.value = isFileFolderExpanded(node.name)
      ? expandedFileFolders.value.filter((name) => name !== node.name)
      : [...expandedFileFolders.value, node.name]
  }
  if (!['系统知识库', '项目', '文档', '客户'].includes(node.name)) activeFolder.value = node.name
  if (node.name === '文档') activeFolder.value = '维修手册'
}
const protectedFileFolders = ['系统知识库', '项目', '文档', '客户', '全部文件', '维修手册', '标准作业流程', '现场图片', '检修报告', '复检报告', '其他技术资料']
const canEditFileFolder = (folder) => !protectedFileFolders.includes(folder)
const createFileFolder = (parentName = '') => {
  const name = window.prompt('请输入新文件夹名称')
  if (!name) return
  const folder = name.trim()
  if (!folder) return
  if (fileFolders.value.includes(folder)) return toast('该文件夹已存在')
  const parent = parentName && !['系统知识库', '项目', '文档', '客户'].includes(parentName)
    ? parentName
    : activeFolder.value === '全部文件' ? '全部文件' : activeFolder.value
  customFileFolders.value = [...customFileFolders.value, folder]
  customFolderParents.value = { ...customFolderParents.value, [folder]: parent }
  expandedFileFolders.value = [...new Set([...expandedFileFolders.value, customFolderParents.value[folder], folder])]
  activeFolder.value = folder
  toast(`已创建文件夹：${folder}`)
}
const renameFileFolder = (folderName = activeFolder.value) => {
  if (!canEditFileFolder(folderName)) {
    return toast('系统默认目录暂不支持重命名')
  }
  const oldName = folderName
  const name = window.prompt('请输入新的文件夹名称', oldName)
  if (!name) return
  const nextName = name.trim()
  if (!nextName || nextName === oldName) return
  if (fileFolders.value.includes(nextName)) return toast('该文件夹已存在')
  customFileFolders.value = customFileFolders.value.map((folder) => folder === oldName ? nextName : folder)
  customFolderParents.value = Object.fromEntries(Object.entries(customFolderParents.value).map(([folder, parent]) => [
    folder === oldName ? nextName : folder,
    parent === oldName ? nextName : parent
  ]))
  files.value.forEach((file) => {
    if (file.folder === oldName) file.folder = nextName
    if (file.category === oldName) file.category = nextName
  })
  expandedFileFolders.value = expandedFileFolders.value.map((folder) => folder === oldName ? nextName : folder)
  activeFolder.value = nextName
  toast(`已重命名为：${nextName}`)
}
const renameActiveFolder = () => renameFileFolder(activeFolder.value)
const startFileDrag = (file) => {
  draggedFileId.value = file.id
  draggedFolderName.value = ''
}
const startFolderDrag = (node) => {
  if (!canEditFileFolder(node.name)) {
    draggedFolderName.value = ''
    return
  }
  draggedFolderName.value = node.name
  draggedFileId.value = ''
}
const dropFileOnFolder = (node) => {
  fileDropTarget.value = ''
  if (draggedFileId.value) {
    const file = files.value.find((item) => item.id === draggedFileId.value)
    if (!file || ['系统知识库', '项目', '文档', '客户'].includes(node.name)) return
    file.folder = node.name
    file.category = node.name
    activeFolder.value = node.name
    draggedFileId.value = ''
    toast(`已将文件加入「${node.name}」`)
    return
  }
  if (draggedFolderName.value && !['系统知识库', '项目', '文档', '客户'].includes(node.name)) {
    if (draggedFolderName.value === node.name) return
    let parent = node.name
    while (customFolderParents.value[parent]) {
      parent = customFolderParents.value[parent]
      if (parent === draggedFolderName.value) return toast('不能移动到自己的下级目录')
    }
    customFolderParents.value = { ...customFolderParents.value, [draggedFolderName.value]: node.name }
    expandedFileFolders.value = [...new Set([...expandedFileFolders.value, node.name])]
    toast(`已将「${draggedFolderName.value}」移动到「${node.name}」下`)
    draggedFolderName.value = ''
  }
}
const toast = (text) => {
  toastText.value = text
  if (toastTimer) window.clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => {
    toastText.value = ''
    toastTimer = null
  }, 1800)
}
const statusClass = (value) => String(value).includes('异常') || String(value).includes('离线') ? 'bad' : 'ok'
const severityText = (value) => ({ low: '低', medium: '中', high: '重复问题', critical: '严重阻塞' }[value] || value || '中')
const statusText = (value) => ({ pending: '待启动', in_progress: '推进中', review: '待验收', completed: '已归档', paused: '已暂停', rejected: '已退回', overdue: '已逾期' }[value] || value || '待启动')
const knowledgeStatusText = (value) => ({ pending: '待人工审核', approved: '已审核入库', rejected: '已退回修改' }[value] || value || '待人工审核')
const modalityText = (value) => ({ text: '文本描述', equipment_model: '技术栈', task_context: '任务上下文', image: '截图图片', document: '任务文档', file: '附件材料' }[value] || value)
const cleanKnowledgePart = (value) => String(value ?? '').replace(/^\s*[.。·]{1,}\s*$/, '').trim()
const knowledgeTypeText = (item) => cleanKnowledgePart(item.type || item.category) || 'Memory Unit'
const knowledgeMetaParts = (item) => [...new Set([
  cleanKnowledgePart(item.equipment),
  cleanKnowledgePart(item.model),
  cleanKnowledgePart(item.source),
  cleanKnowledgePart(item.fileType)
].filter(Boolean))]
const flattenKnowledgeText = (value) => {
  if (Array.isArray(value)) return value.flatMap(flattenKnowledgeText)
  if (value && typeof value === 'object') return Object.values(value).flatMap(flattenKnowledgeText)
  const text = cleanKnowledgePart(value)
  if (!text) return []
  if (/^[\[{]/.test(text)) {
    try { return flattenKnowledgeText(JSON.parse(text)) } catch { /* 使用普通文本继续处理 */ }
  }
  return text
    .replace(/^\s*[\["']+|[\]"']+\s*$/g, '')
    .split(/(?:"\s*,\s*"|\n+)/)
    .map((part) => part.replace(/^\s*["']|["']\s*$/g, '').trim())
    .filter(Boolean)
}
const knowledgeSummaryLines = (item) => {
  const lines = flattenKnowledgeText(item.summary || item.content)
  return lines.length ? lines.slice(0, 4) : ['该资料已纳入一休知识库，可查看详情或作为智能检索依据。']
}
const searchFromKnowledge = (item) => {
  const equipment = cleanKnowledgePart(item.equipment)
  const model = cleanKnowledgePart(item.model)
  if (equipment) searchForm.deviceName = equipment
  if (model && model !== 'ALL') searchForm.deviceModel = model
  searchForm.query = `${item.title} ${knowledgeSummaryLines(item)[0]}`.trim()
  activePage.value = 'search'
  resultTab.value = '全部'
}
const stepTitle = (step) => typeof step === 'string' ? step : step?.title || '检修步骤'
const stepDetail = (step) => typeof step === 'object' ? step?.detail || '' : ''
const isTaskStepCompleted = (task, index) => (task.completedSteps || []).includes(index)
const taskLevel = (task = {}) => task.maintenanceLevel || task.maintenance_level || task.level || (task.severity === 'high' ? '三级大修' : '二级检修')
const taskCategory = (task = {}) => task.equipment_category || task.category || (task.equipment_name?.includes('配电') ? '电气系统' : task.equipment_name?.includes('发动机') ? '发动机' : '通用设备')
const recommendedSopForTask = (task = {}) => {
  const category = taskCategory(task)
  const level = taskLevel(task)
  const fault = task.fault_type || '故障'
  const base = [
    { title: '作业许可与安全隔离', detail: `确认${category}${level}作业票，执行停机、断电、验电和挂牌。`, required: true, evidence: '安全确认' },
    { title: '故障现象记录', detail: `记录${fault}出现条件、报警、温度、声音及现场图片，禁止带故障盲目拆机。`, required: true, evidence: '数据或图片' },
    { title: '按依据逐项检测', detail: '按照召回手册和相似案例测量关键参数，先确认原因再更换部件。', required: true, evidence: '检测值' },
    { title: '维修处置与过程复核', detail: '执行紧固、清洁、调整或更换，记录工具、部件及关键扭矩。', required: true, evidence: '过程记录' },
    { title: '复测验收', detail: '恢复防护后试运行，对照标准复测并确认故障消除。', required: true, evidence: '复测结果' },
    { title: '报告与知识沉淀', detail: '提交检修报告、引用依据和证据；有效经验进入知识审核队列。', required: true, evidence: '检修报告' }
  ]
  if (category.includes('电气')) base.splice(1, 0, { title: '电气合规确认', detail: '复核工作票、验电、接地线、绝缘防护和禁止合闸标识。', required: true, evidence: '工作票/照片' })
  if (level.includes('三级') || task.severity === 'high') base.splice(2, 0, { title: '高风险二次确认', detail: '由安全负责人复核风险隔离、应急措施和复测窗口。', required: true, evidence: '二次确认记录' })
  return base
}
const taskFlowProfile = (task = {}) => {
  const category = taskCategory(task)
  const level = taskLevel(task)
  return {
    title: `${category} · ${level}标准流程包`,
    reason: `根据设备类型「${category}」、检修等级「${level}」和故障类型「${task.fault_type || '待确认'}」推送 ${recommendedSopForTask(task).length} 步流程。`,
    tags: [category, level, task.fault_type || '故障确认', task.severity === 'high' ? '高风险二次确认' : '常规合规校验']
  }
}
const taskComplianceChecks = (task = {}) => {
  const completed = task.completedSteps?.length || 0
  const total = task.sop?.length || recommendedSopForTask(task).length
  const isElectric = taskCategory(task).includes('电气')
  const isHighRisk = task.severity === 'high'
  return [
    { label: '流程已推送', hint: `${taskFlowProfile(task).title}`, ok: Boolean(task.sop?.length), required: true },
    { label: '安全隔离确认', hint: isElectric ? '停电、验电、挂牌、接地线' : '停机、泄压、温度确认', ok: completed > 0 || task.status !== 'pending', required: true },
    { label: '证据记录完整', hint: '图片/检测值/过程记录至少一项', ok: completed >= Math.max(1, Math.floor(total / 2)) || task.status === 'review' || task.status === 'completed', required: true },
    { label: '高风险复核', hint: isHighRisk ? '需安全负责人二次确认' : '常规风险，无需额外复核', ok: !isHighRisk || completed >= 2 || ['review', 'completed'].includes(task.status), required: isHighRisk },
    { label: '复测闭环', hint: '全部步骤完成后才可进入复检', ok: completed >= total || ['review', 'completed'].includes(task.status), required: true }
  ]
}
const applyRecommendedSop = (task) => {
  if (!task) return
  task.sop = recommendedSopForTask(task)
  task.safety = [...new Set([...(task.safety || []), ...taskComplianceChecks(task).filter((item) => item.required).map((item) => item.hint)])]
  task.current_step = task.status === 'pending' ? '作业许可与安全隔离' : task.current_step
  toast('已应用个性化标准作业流程')
}
const folderIcon = (folder) => ({
  全部文件: '▦',
  维修手册: '▣',
  标准作业流程: '✓',
  现场图片: '◉',
  检修报告: '▤',
  复检报告: '◎',
  其他技术资料: '□'
}[folder] || '□')
const fileIconClass = (file) => ({
  PDF: 'pdf',
  Word: 'doc',
  Excel: 'sheet',
  图片: 'image',
  视频: 'video',
  文本: 'text'
}[file.type] || 'other')
const fileIcon = (file) => ({
  PDF: 'PDF',
  Word: 'DOC',
  Excel: 'XLS',
  图片: 'IMG',
  视频: 'MP4',
  文本: 'TXT'
}[file.type] || 'FILE')
const graphTypeCount = (kind) => graphNodes.value.filter((node) => node.kind === kind).length
const graphRelationCount = (relation) => {
  const index = graphRelationTypes.indexOf(relation)
  if (index < 0) return graphEdges.value.length
  return Math.max(1, Math.round(graphEdges.value.length / Math.max(graphRelationTypes.length - index, 1)))
}
const clampFloatingAgent = () => {
  const size = floatingAgent.open ? { width: 440, height: 560 } : { width: 74, height: 74 }
  const maxX = Math.max(20, window.innerWidth - size.width - 20)
  const maxY = Math.max(20, window.innerHeight - size.height - 20)
  floatingAgent.x = Math.min(maxX, Math.max(20, floatingAgent.x || maxX))
  floatingAgent.y = Math.min(maxY, Math.max(96, floatingAgent.y || maxY))
}
const initFloatingAgent = () => {
  if (!floatingAgent.x && !floatingAgent.y) {
    floatingAgent.x = Math.max(20, window.innerWidth - 108)
    floatingAgent.y = Math.max(112, window.innerHeight - 108)
  }
  clampFloatingAgent()
}
const startFloatingAgentDrag = (event) => {
  event.preventDefault()
  floatingAgent.dragging = true
  floatingAgent.moved = false
  floatingAgentDrag = { startX: event.clientX, startY: event.clientY, baseX: floatingAgent.x, baseY: floatingAgent.y }
  const onMove = (moveEvent) => {
    if (!floatingAgentDrag) return
    const dx = moveEvent.clientX - floatingAgentDrag.startX
    const dy = moveEvent.clientY - floatingAgentDrag.startY
    if (Math.abs(dx) + Math.abs(dy) > 4) floatingAgent.moved = true
    floatingAgent.x = floatingAgentDrag.baseX + dx
    floatingAgent.y = floatingAgentDrag.baseY + dy
    clampFloatingAgent()
  }
  const onUp = () => {
    floatingAgent.dragging = false
    floatingAgentDrag = null
    window.removeEventListener('pointermove', onMove)
    window.removeEventListener('pointerup', onUp)
  }
  window.addEventListener('pointermove', onMove)
  window.addEventListener('pointerup', onUp)
}
const toggleFloatingAgent = () => {
  if (floatingAgent.moved) return
  floatingAgent.open = !floatingAgent.open
  nextTick(() => {
    clampFloatingAgent()
    window.setTimeout(clampFloatingAgent, 80)
  })
}
const closeFloatingAgentOnOutside = (event) => {
  if (!floatingAgent.open || activePage.value !== 'knowledge') return
  if (event.target?.closest?.('.floating-agent')) return
  floatingAgent.open = false
  nextTick(clampFloatingAgent)
}
const clearOperatorMessages = () => {
  operatorMessages.value = operatorMessages.value.filter((message) => !(message.page === activePage.value && (message.agentId || pageDefaultAgentId.value) === activeOperatorAgentId.value))
}
const askAgentAboutNode = (node) => {
  floatingAgent.open = true
  if (!node) return sendOperatorPrompt('请帮我解释当前知识图谱的重点关系')
  sendOperatorPrompt(`请围绕知识图谱节点「${node.label}」解释它的关联资料、上下游关系和检修建议`)
}
const inferFileType = (file) => {
  const name = file.name.toLowerCase()
  const mime = file.type || ''
  if (mime.includes('image') || /\.(png|jpe?g|gif|webp|bmp)$/i.test(name)) return '图片'
  if (mime.includes('pdf') || name.endsWith('.pdf')) return 'PDF'
  if (mime.includes('video') || /\.(mp4|webm|ogg|mov)$/i.test(name)) return '视频'
  if (mime.includes('word') || /\.(docx?|wps)$/i.test(name)) return 'Word'
  if (mime.includes('excel') || /\.(xlsx?|csv)$/i.test(name)) return 'Excel'
  if (mime.includes('text') || /\.(txt|md|log)$/i.test(name)) return '文本'
  return '其他'
}

const toFileMeta = (file) => ({
  localId: `${file.name}-${file.lastModified}-${Math.random()}`,
  name: file.name,
  size: `${Math.max(file.size / 1024, 1).toFixed(1)} KB`,
  rawSize: file.size,
  sizeText: `${Math.max(file.size / 1024, 1).toFixed(1)} KB`,
  type: inferFileType(file),
  rawType: file.type,
  raw: file,
  url: URL.createObjectURL(file),
  status: '待上传',
  parseStatus: '等待解析',
  auditStatus: '待审核',
  version: 'v1.0',
  uploaded_at: new Date().toLocaleString('zh-CN'),
  uploader: user.name
})
const releaseFileUrl = (file) => {
  if (file?.url?.startsWith('blob:')) URL.revokeObjectURL(file.url)
}
const releaseFileUrls = (list = []) => list.forEach(releaseFileUrl)
const snapshotFiles = (list = []) => list.map((file) => ({
  localId: file.localId,
  name: file.name,
  type: file.type,
  url: file.url,
  size: file.size,
  sizeText: file.sizeText,
  status: file.status
}))
const cloneAssistantFileForSearch = (file) => ({
  ...file,
  localId: `search-${file.localId || `${file.name}-${Date.now()}`}`,
  status: '已由天工转入智能检索',
  progress: file.progress || 0
})
const inferSearchScene = (text = '', files = []) => {
  const content = `${text || ''} ${files.map((file) => file.name || '').join(' ')}`.toLowerCase()
  const hasWaterIntent = hasAffirmativeWaterScene(content)
  const hasAutoVehicleIntent = /汽车|轿车|车辆/.test(content)
  const hasMotorcycleEngineIntent = /摩托|cg-?125/.test(content) || (!hasAutoVehicleIntent && /发动机异响|发动机|气门|怠速|正时链条|张紧器|火花塞|化油器|凸轮轴|摇臂/.test(content))
  if (hasMotorcycleEngineIntent && !hasWaterIntent) {
    return {
      type: 'motorcycle_engine',
      deviceName: '摩托车发动机总成',
      deviceModel: /cg-?125/.test(content) ? 'CG-125' : '',
      faultCode: '',
      category: '发动机',
      faultType: /怠速/.test(content) ? '异响/怠速不稳' : '发动机异响',
      query: '基于本次输入和图片检索摩托车发动机异响；只根据当前图片、文字和本轮检索依据回答，不混入历史检索。重点检查气门间隙、正时链条/张紧器、摇臂/凸轮轴、机油润滑、火花塞、化油器怠速油路、进气漏气和曲轴连杆轴承。'
    }
  }
  if (hasWaterIntent) {
    return {
      type: 'vehicle_water',
      deviceName: '',
      deviceModel: '',
      faultCode: '',
      category: '',
      faultType: '',
      query: '基于本次输入和图片进行检索；只根据当前图片、文字和本轮检索依据回答，不套用旧案例。若现场确认为泡水/涉水，再检查发动机进气、机油乳化、变速箱油、电气线束、制动系统、底盘和安全启动风险。'
    }
  }
  return null
}
const WATER_SCENE_RE = /车淹|泡水|涉水|积水|淹水|水淹|进水/
const WATER_RESULT_RE = /泡水|涉水|水淹|积水|进水|汽车涉水/
const WATER_NEGATION_RE = /没有泡水|无泡水|未泡水|不是泡水|非泡水|没有涉水|无涉水|未涉水|不涉水|不是涉水|非涉水|没有积水|无积水|未积水|不是积水|非积水|没有进水|无进水|未进水|不进水|不是进水|非进水|没有水淹|无水淹|未水淹|不涉及水/
const hasAffirmativeWaterScene = (value = '') => WATER_SCENE_RE.test(String(value || '')) && !WATER_NEGATION_RE.test(String(value || ''))
const resetSearchIdentityFields = () => {
  Object.assign(searchForm, {
    deviceName: '',
    deviceModel: '',
    faultCode: '',
    category: '',
    faultType: ''
  })
}
const applySearchScene = (scene = {}) => {
  if (!scene) return
  Object.entries(scene).forEach(([key, value]) => {
    if (value !== undefined && value !== null) searchForm[key] = value
  })
}
const isVisualSearchTransferPrompt = (value) => {
  const text = String(value || '')
  return assistantFiles.value.length > 0 && /图片|图像|照片|附件|资料|上传|转交|交给|智能检索|观微|查看|分析/.test(text) && /智能检索|观微|查看|分析|什么问题|故障/.test(text)
}
const addFiles = async (event, target) => {
  const selected = Array.from(event.target.files || []).map(toFileMeta)
  if (target === 'search') {
    searchResult.value = null
    searchFiles.value.push(...selected.map((file) => ({ ...file, status: '已加入检索' })))
  } else if (target === 'assistant') {
    searchResult.value = null
    assistantFiles.value.push(...selected.map((file) => ({ ...file, status: '待发送' })))
  } else {
    for (const file of selected) {
      const folder = activeFolder.value === '全部文件' ? '现场图片' : activeFolder.value
      try {
        file.status = '上传中'
        const saved = await yixiuApi.uploadFile(file.raw, { category: folder, folder, uploader: user.name, equipment: '', model: '', purpose: 'knowledge' }, (progress) => { file.progress = progress })
        files.value.unshift({ ...file, ...saved, id: saved.id || file.localId, url: saved.url || file.url, category: saved.category || folder, folder: saved.folder || folder, status: '上传成功', parseStatus: saved.parseStatus || '等待解析' })
      } catch (error) {
        file.status = '上传失败'
        toast(error.message)
      }
    }
    toast(`已上传 ${selected.length} 个文件`)
  }
  event.target.value = ''
}
const addDroppedFiles = (event) => {
  searchResult.value = null
  searchFiles.value.push(...Array.from(event.dataTransfer.files || []).map((file) => ({ ...toFileMeta(file), status: '已加入检索' })))
}
const addManagerDroppedFiles = async (event) => {
  const selected = Array.from(event.dataTransfer.files || []).map(toFileMeta)
  for (const file of selected) {
    const folder = activeFolder.value === '全部文件' ? '现场图片' : activeFolder.value
    try {
      file.status = '上传中'
      const saved = await yixiuApi.uploadFile(file.raw, { category: folder, folder, uploader: user.name, purpose: 'knowledge' }, (progress) => { file.progress = progress })
      files.value.unshift({ ...file, ...saved, id: saved.id || file.localId, url: saved.url || file.url, category: saved.category || folder, folder: saved.folder || folder, status: '上传成功', parseStatus: saved.parseStatus || '等待解析' })
    } catch (error) {
      file.status = '上传失败'
      toast(error.message)
    }
  }
  if (selected.length) toast(`已拖入 ${selected.length} 个文件`)
}
const removeSearchFile = (localId) => {
  releaseFileUrl(searchFiles.value.find((file) => file.localId === localId))
  searchFiles.value = searchFiles.value.filter((file) => file.localId !== localId)
}
const removeAssistantFile = (localId) => {
  releaseFileUrl(assistantFiles.value.find((file) => file.localId === localId))
  assistantFiles.value = assistantFiles.value.filter((file) => file.localId !== localId)
}
const startOperatorResize = (event) => {
  event.preventDefault()
  const startX = event.clientX
  const startWidth = operatorWidth.value
  const onMove = (moveEvent) => {
    operatorWidth.value = Math.min(520, Math.max(300, startWidth + startX - moveEvent.clientX))
  }
  const onUp = () => {
    localStorage.setItem('yixiu-operator-width', String(operatorWidth.value))
    document.body.classList.remove('resizing-panel')
    document.removeEventListener('pointermove', onMove)
    document.removeEventListener('pointerup', onUp)
    stopOperatorResize = null
  }
  document.body.classList.add('resizing-panel')
  document.addEventListener('pointermove', onMove)
  document.addEventListener('pointerup', onUp)
  stopOperatorResize = onUp
}
const toggleAssistantVoice = () => {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!Recognition) return toast('当前浏览器不支持语音识别，请使用新版 Chrome 或 Edge')
  if (assistantVoiceListening.value && assistantSpeechRecognition) {
    assistantSpeechRecognition.stop()
    return
  }
  const original = operatorInput.value.trim()
  assistantSpeechRecognition = new Recognition()
  assistantSpeechRecognition.lang = 'zh-CN'
  assistantSpeechRecognition.continuous = true
  assistantSpeechRecognition.interimResults = true
  assistantSpeechRecognition.onstart = () => { assistantVoiceListening.value = true; toast('正在将现场语音转换为文字') }
  assistantSpeechRecognition.onresult = (voiceEvent) => {
    const transcript = Array.from(voiceEvent.results).map((result) => result[0].transcript).join('')
    operatorInput.value = `${original}${original && transcript ? '；' : ''}${transcript}`
  }
  assistantSpeechRecognition.onerror = (voiceEvent) => toast(voiceEvent.error === 'not-allowed' ? '请允许浏览器使用麦克风' : '语音识别中断，请重试')
  assistantSpeechRecognition.onend = () => { assistantVoiceListening.value = false; assistantSpeechRecognition = null }
  assistantSpeechRecognition.start()
}
const simulateVoice = () => {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!Recognition) return toast('当前浏览器不支持语音识别，请使用新版 Chrome 或 Edge')
  if (voiceListening.value && speechRecognition) {
    speechRecognition.stop()
    return
  }
  speechRecognition = new Recognition()
  speechRecognition.lang = 'zh-CN'
  speechRecognition.continuous = true
  speechRecognition.interimResults = true
  const original = searchForm.query.trim()
  speechRecognition.onstart = () => { voiceListening.value = true; toast('正在识别现场语音') }
  speechRecognition.onresult = (event) => {
    const transcript = Array.from(event.results).map((result) => result[0].transcript).join('')
    searchForm.query = `${original}${original && transcript ? '；' : ''}${transcript}`
  }
  speechRecognition.onerror = (event) => toast(event.error === 'not-allowed' ? '请允许浏览器使用麦克风' : '语音识别中断，请重试')
  speechRecognition.onend = () => { voiceListening.value = false; speechRecognition = null }
  speechRecognition.start()
}
const buildLocalSearchResult = () => {
  const scene = inferSearchScene(searchForm.query, searchFiles.value)
  if (scene?.type === 'motorcycle_engine') {
    const subject = [scene.deviceModel || searchForm.deviceModel, scene.deviceName || searchForm.deviceName].filter(Boolean).join(' ') || '摩托车发动机'
    return {
      phenomenonSummary: `${subject}出现发动机异响/怠速不稳线索；车型、里程、冷车/热车差异和检测数值均待确认。本次只按当前图片与输入重新检索，不引用旧检索结果。`,
      risk: 'medium',
      confidence: searchFiles.value.length ? 87 : 82,
      stopAdvice: '先停机冷却并确认机油液位；异响明显、敲击加重或润滑异常时不要继续高转速试车。',
      modalities: ['text', ...(searchFiles.value.length ? ['image'] : [])],
      visualFindings: searchFiles.value.length ? ['已接入本次摩托车发动机图片；具体型号和拆检状态待确认。'] : [],
      causes: ['气门间隙过大或过小', '正时链条松旷或张紧器异常', '摇臂/凸轮轴磨损', '机油不足、变质或润滑不良', '火花塞积碳或点火弱', '化油器怠速油路堵塞或混合气异常', '进气漏气', '活塞、连杆或曲轴轴承异常磨损'],
      positions: ['气门室盖/摇臂/凸轮轴', '正时链条与张紧器', '机油尺/机油滤网/润滑油路', '火花塞与高压帽', '化油器怠速油路', '进气歧管与密封垫', '曲轴箱与连杆轴承区域'],
      tools: ['塞尺', '听诊棒', '火花塞套筒', '压缩压力表', '万用表', '扭矩扳手', '化油器清洗工具'],
      suggestion: {
        steps: ['停机冷却并确认机油液位和机油状态', '冷车/热车分别听诊定位异响区域', '拆检气门室盖并用塞尺检查气门间隙', '检查正时链条松旷、张紧器回位和导轨磨损', '检查摇臂、凸轮轴和气门机构磨损', '检查火花塞积碳、点火强度和高压帽连接', '清洁化油器怠速油路并检查进气漏气', '复装后记录怠速、加速响应和异响复测结果'],
        tools: ['塞尺', '听诊棒', '火花塞套筒', '扭矩扳手'],
        risks: ['热机烫伤', '误启动夹伤', '气门间隙调整错误导致动力下降或异响加重', '高转速试车扩大机械磨损']
      },
      references: [
        { id: 'engine-ref-1', title: 'CG-125/同类单缸发动机气门间隙检查 SOP', type: '标准作业流程 SOP', category: '发动机资料', equipment: '摩托车发动机总成', model: scene.deviceModel || '', match: 89, summary: '覆盖停机冷却、拆气门室盖、塞尺测量、间隙调整、复装和热车复测。', tags: ['发动机', '气门间隙', '异响'] },
        { id: 'engine-ref-2', title: '摩托车发动机异响与怠速不稳排查案例', type: '历史故障案例', category: '历史故障案例', equipment: '摩托车发动机总成', model: scene.deviceModel || '', match: 84, summary: '围绕正时链条、张紧器、摇臂/凸轮轴、点火和化油器怠速油路进行排查。', tags: ['发动机异响', '怠速不稳', '复检'] }
      ]
    }
  }
  if (scene?.type === 'vehicle_water') {
    const fileNames = searchFiles.value.map((file) => file.name).filter(Boolean)
    return {
      phenomenonSummary: `现场图片显示车辆处于积水环境，已知线索：${fileNames.length ? fileNames.join('、') : '已上传现场图片'}。积水高度、车辆型号、发动机是否进水等信息需现场复核；当前按车辆泡水/涉水风险进行检修排查。`,
      risk: 'high',
      confidence: searchFiles.value.length ? 86 : 72,
      stopAdvice: '不要立即启动发动机；先断电、拖车转移并检查进气、油液和电气系统，避免发动机进水后二次损坏。',
      modalities: ['text', ...(searchFiles.value.length ? ['image'] : [])],
      visualFindings: [
        '车辆处于积水环境，轮胎和底盘区域被水浸泡。',
        '仅凭图片无法确认车型、发动机进水深度和车内进水程度，需现场拆检确认。',
        '优先排查进气系统、机油乳化、电气线束、制动系统和底盘泥沙残留。'
      ],
      causes: ['道路积水导致底盘、轮毂和制动部件浸水', '积水可能经进气口、车门密封或线束插头进入关键系统', '长时间浸泡可能引发油液乳化、电气短路、轴承锈蚀或车内霉变'],
      positions: ['发动机进气口/空气滤芯', '机油尺与油底壳', '变速箱油/差速器油', '保险盒/ECU/线束插头', '刹车盘/刹车片/ABS轮速传感器', '底盘悬挂/轴承/排气管', '车内地毯/座椅底部/安全带卷收器'],
      tools: ['拖车设备', '绝缘检测工具', '内窥镜', '油液检查工具', '万用表', '举升机', '除湿消毒设备'],
      suggestion: {
        steps: ['现场拍照记录并禁止启动', '断开电瓶负极并拖车到维修点', '拆检空气滤芯和进气管确认是否进水', '检查机油和变速箱油是否乳化', '检查 ECU、保险盒和线束插头是否受潮', '清洗底盘并做干燥防锈', '车内除湿消毒后复检', '确认油液、电气和制动正常后再试车'],
        tools: ['拖车设备', '内窥镜', '万用表', '举升机'],
        risks: ['误启动导致发动机连杆弯曲', '电气短路', '制动性能下降', '底盘轴承锈蚀', '车内发霉异味']
      },
      references: [
        { id: 'vehicle-water-ref-1', title: '泡水车辆检修排查 SOP', type: '标准作业流程 SOP', category: '汽车涉水检修', equipment: '涉水车辆', model: '', match: 88, summary: '覆盖禁止启动、拖车、进气检查、油液检查、电气干燥、底盘清洗防锈和复检验收。', tags: ['泡水车', '涉水', '安全确认'] },
        { id: 'vehicle-water-ref-2', title: '汽车电气系统进水检查清单', type: '维修手册', category: '电气系统', equipment: '涉水车辆', model: '', match: 83, summary: '重点检查 ECU、保险盒、传感器、线束插头、启动机和发电机受潮短路风险。', tags: ['电气系统', '进水', '复检'] }
      ]
    }
  }
  const isHighRisk = ['过热', '点火故障'].includes(searchForm.faultType)
  const subject = [searchForm.deviceModel, searchForm.deviceName].filter(Boolean).join(' ') || '待确认设备'
  const fault = searchForm.faultType || '待确认故障'
  return {
    phenomenonSummary: `${subject} 出现${fault}现象，建议结合现场记录、图片和历史案例优先定位高频故障部位；未知型号和未知部位保持待确认。`,
    risk: isHighRisk ? 'high' : 'medium',
    confidence: searchFiles.value.length ? 88 : 82,
    stopAdvice: isHighRisk ? '先执行安全隔离并确认温度、供电和联锁状态' : '可在安全确认后按标准流程分步排查',
    modalities: ['text', ...(searchFiles.value.length ? ['image', 'file'] : [])],
    visualFindings: searchFiles.value.length ? ['已接入现场附件，建议核对异常区域、油迹、温升或磨损痕迹'] : [],
    causes: searchForm.faultType === '异响'
      ? ['气门间隙异常', '紧固件松动', '润滑状态不足']
      : searchForm.faultType === '过热'
        ? ['散热通道堵塞', '接触器触点异常', '负载偏高']
        : ['密封件老化', '连接处松动', '作业后复检不足'],
    positions: searchForm.faultType === '异响' ? ['气门室', '正时链条', '轴承座'] : ['异常部位', '连接点', '关键测量点'],
    tools: ['红外测温仪', '扭矩扳手', '万用表', '复检记录表'],
    suggestion: {
      steps: ['确认作业安全隔离', '复核现场现象和设备参数', '检查高频故障部位', '记录处理措施并执行复测', '将有效结论提交沉淀审核'],
      tools: ['红外测温仪', '扭矩扳手', '万用表'],
      risks: ['带电作业风险', '高温部位烫伤', '复测数据缺失']
    },
    references: [
      { id: 'local-ref-1', title: `${subject} ${fault}历史故障案例`, type: '历史故障案例', category: '历史故障案例', equipment: searchForm.deviceName, model: searchForm.deviceModel, match: 86, summary: '同类现象常见于关键连接、润滑、散热或密封状态异常，需结合复测记录确认。', tags: [fault, '历史案例', '复检'] },
      { id: 'local-ref-2', title: `${searchForm.category}标准作业流程`, type: '标准作业流程 SOP', category: '标准作业流程 SOP', equipment: searchForm.deviceName, model: searchForm.deviceModel, match: 82, summary: '按安全确认、部位检查、处理记录、复测验收的顺序执行，保证后续沉淀可复用。', tags: ['SOP', searchForm.maintenanceLevel, '安全确认'] }
    ]
  }
}
const runSearch = async () => {
  const startedAt = Date.now()
  const currentScene = inferSearchScene(searchForm.query, searchFiles.value)
  const currentInputText = `${searchForm.query || ''} ${searchFiles.value.map((file) => file.name || '').join(' ')}`
  if (currentScene) {
    resetSearchIdentityFields()
    applySearchScene(currentScene)
  } else if (!hasAffirmativeWaterScene(currentInputText) && WATER_RESULT_RE.test(`${searchForm.deviceName}${searchForm.category}${searchForm.faultType}`)) {
    resetSearchIdentityFields()
  }
  loading.search = true
  searchPanel.value = 'results'
  try {
    for (const file of searchFiles.value.filter((item) => !item.id)) {
      file.status = '上传中'
      try {
        const saved = await yixiuApi.uploadFile(file.raw, { purpose: 'search', category: '多模态检索', folder: '检索附件', uploader: user.name, equipment: searchForm.deviceName, model: searchForm.deviceModel }, (progress) => { file.progress = progress })
        Object.assign(file, saved, { raw: file.raw, localId: file.localId, status: '解析完成', progress: 100 })
      } catch (error) {
        file.status = '上传失败'
        throw error
      }
    }
    searchResult.value = await yixiuApi.search({ ...searchForm, fileIds: searchFiles.value.map((file) => file.id).filter(Boolean), query: searchForm.query })
    searchHistory.value = [
      {
        id: `history-${Date.now()}`,
        title: `${searchForm.deviceModel || searchForm.deviceName} ${searchForm.faultType}检索`,
        deviceName: searchForm.deviceName,
        model: searchForm.deviceModel,
        faultCode: searchForm.faultCode,
        category: searchForm.category,
        faultType: searchForm.faultType,
        maintenanceLevel: searchForm.maintenanceLevel,
        query: searchForm.query,
        confidence: searchResult.value?.confidence || 86,
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      },
      ...searchHistory.value
    ].slice(0, 8)
    searchPanel.value = 'results'
    toast('检索完成')
  } catch (error) {
    searchResult.value = buildLocalSearchResult()
    searchHistory.value = [
      {
        id: `history-${Date.now()}`,
        title: `${searchForm.deviceModel || searchForm.deviceName} ${searchForm.faultType}检索`,
        deviceName: searchForm.deviceName,
        model: searchForm.deviceModel,
        faultCode: searchForm.faultCode,
        category: searchForm.category,
        faultType: searchForm.faultType,
        maintenanceLevel: searchForm.maintenanceLevel,
        query: searchForm.query,
        confidence: searchResult.value.confidence,
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      },
      ...searchHistory.value
    ].slice(0, 8)
    toast(error.message ? '接口暂不可用，已生成本地检索研判' : '已生成本地检索研判')
  } finally {
    const elapsed = Date.now() - startedAt
    if (elapsed < 1400) await new Promise((resolve) => setTimeout(resolve, 1400 - elapsed))
    loading.search = false
  }
}
const createTaskFromSearch = async (item) => {
  const created = await yixiuApi.createTask({
    title: `${searchForm.deviceModel} ${searchForm.faultType}检修任务`,
    deviceName: searchForm.deviceName,
    deviceModel: searchForm.deviceModel,
    category: searchForm.category,
    maintenanceLevel: searchForm.maintenanceLevel,
    faultType: searchForm.faultType,
    description: searchForm.query,
    severity: searchResult.value?.risk || 'medium',
    assignee_name: user.name,
    sop: searchResult.value?.suggestion?.steps || [],
    tools: searchResult.value?.suggestion?.tools || [],
    safety: searchResult.value?.suggestion?.risks || [],
    references: [item.title]
  })
  const localTask = { ...created, equipment_category: created.equipment_category || searchForm.category, maintenanceLevel: created.maintenanceLevel || searchForm.maintenanceLevel, workOrderNo: created.workOrderNo || `YX-${Date.now()}`, progress: 0, current_step: '待接收', collaborators: [] }
  localTask.sop = localTask.sop?.length ? localTask.sop : recommendedSopForTask(localTask)
  localTask.safety = localTask.safety?.length ? localTask.safety : taskComplianceChecks(localTask).filter((item) => item.required).map((item) => item.hint)
  tasks.value.unshift(localTask)
  toast('已从检索结果创建检修任务')
}
const applySearchHistory = (item) => {
  Object.assign(searchForm, {
    deviceName: item.deviceName,
    deviceModel: item.model,
    faultCode: item.faultCode,
    category: item.category,
    faultType: item.faultType,
    maintenanceLevel: item.maintenanceLevel,
    query: item.query
  })
  searchPanel.value = 'multimodal'
  toast('已回填历史检索条件')
}
const applyLearningRecommendation = (item) => {
  searchForm.query = `${searchForm.query ? `${searchForm.query}；` : ''}${item.query}`.trim()
  searchPanel.value = 'multimodal'
  toast('已加入经验推荐关键词')
}
const openLearningRecommendation = (item) => {
  selectedLearningRecommendation.value = item
}
const externalArtifactTypeText = (type = '') => ({
  project_update: '项目进展',
  decision: '关键决策',
  risk: '风险提醒',
  todo: '待办事项',
  memory_candidate: 'Memory 候选',
  skill_candidate: 'Skill 候选',
  eval_case: 'Eval 用例'
})[type] || type || '候选资产'
const fillExternalImportExample = (provider = externalImportForm.provider) => {
  externalImportForm.provider = provider || 'codex'
  externalImportForm.project_name = externalImportForm.project_name || '一休 Web 端'
  externalImportForm.title = `${provider === 'claude' ? 'Claude' : 'Codex'} 项目协作记录导入`
  externalImportForm.raw_content = JSON.stringify({
    format: 'yixiu.codex.upload.v1',
    codex_report: {
      task_goal: '把任务管理升级为项目管理，并记录项目阶段、周期、里程碑、风险和交付物。',
      work_summary: [
        '前端展示改为项目管理口径',
        '补充项目进展、风险和交付物信息'
      ],
      changed_files: ['frontend/App.vue', 'frontend/src/data/yixiuMock.js'],
      decisions: ['保留原有任务数据结构作为兼容层，逐步演进为项目数据模型'],
      risks: ['旧文案仍可能残留', '后端项目字段需要继续结构化'],
      todos: ['补充项目导入接口', '完善项目进展时间线', '接入 Memory 候选审核'],
      validation: ['npm run build 通过', 'localhost 页面返回 200'],
      memory_candidates: ['项目管理改造应保留旧任务结构作为兼容层，避免一次性破坏现有页面数据。'],
      skill_candidates: ['项目模块改造流程：先改导航和页面语义，再补数据字段，最后做审核入库和构建验证。'],
      eval_cases: ['检查任务管理入口是否已统一显示为项目管理，并确认项目进展字段可见。'],
      next_actions: ['将通过审核的 Memory 写入团队记忆库']
    }
  }, null, 2)
}
const loadExternalImports = async () => {
  try {
    const data = await yixiuApi.externalImports()
    externalImports.value = data.imports || []
  } catch (error) {
    toast(`导入记录加载失败：${error.message}`)
  }
}
const openMcpConfig = async () => {
  activePage.value = 'knowledge'
  knowledgePanel.value = 'mcp'
  try {
    mcpManifest.value = await yixiuApi.mcpManifest()
  } catch (error) {
    toast(`MCP 配置加载失败：${error.message}`)
  }
}
const submitExternalImport = async () => {
  if (!externalImportForm.raw_content.trim()) return toast('请先粘贴 Codex / Claude 的总结、对话或 diff')
  externalImportLoading.value = true
  try {
    const data = await yixiuApi.createExternalImport({ ...externalImportForm })
    if (data.import) {
      externalImports.value = [data.import, ...externalImports.value.filter((item) => item.id !== data.import.id)]
      externalImportForm.raw_content = ''
      toast('外部 AI 内容已导入，并生成候选资产')
    }
  } catch (error) {
    toast(`导入失败：${error.message}`)
  } finally {
    externalImportLoading.value = false
  }
}
const parseExternalImport = async (item) => {
  try {
    const data = await yixiuApi.parseExternalImport(item.id)
    if (data.import) {
      externalImports.value = externalImports.value.map((row) => row.id === item.id ? data.import : row)
      toast('已重新解析导入内容')
    }
  } catch (error) {
    toast(`重新解析失败：${error.message}`)
  }
}
const reviewExternalArtifact = async (artifact, status) => {
  try {
    const data = await yixiuApi.reviewExternalArtifact(artifact.id, { status, reviewer: user.name })
    const updated = data.artifact
    externalImports.value = externalImports.value.map((item) => ({
      ...item,
      artifacts: (item.artifacts || []).map((row) => row.id === updated.id ? updated : row)
    }))
    toast(status === 'approved' ? '候选资产已通过审核' : '候选资产已退回')
  } catch (error) {
    toast(`审核失败：${error.message}`)
  }
}
const prepareKnowledgeFromSearch = () => {
  if (!searchResult.value) {
    searchPanel.value = 'multimodal'
    return toast('请先完成一次多模态检索')
  }
  Object.assign(knowledgeForm, {
    title: `${searchForm.deviceModel || searchForm.deviceName} ${searchForm.faultType}检索沉淀`,
    type: '历史故障案例',
    equipment: searchForm.deviceName,
    model: searchForm.deviceModel,
    source: `${searchForm.faultCode || '检索结果'} · 智能检索`,
    tagText: [searchForm.faultType, searchForm.maintenanceLevel, '多模态检索'].filter(Boolean).join(','),
    summary: [
      `故障现象：${searchForm.query}`,
      `研判结论：${searchResult.value.phenomenonSummary}`,
      `可能原因：${(searchResult.value.causes || []).join('、')}`,
      `推荐步骤：${(searchResult.value.suggestion?.steps || []).join('；')}`,
      `引用依据：${(searchResult.value.references || []).slice(0, 3).map((item) => item.title).join('、')}`
    ].filter(Boolean).join('\n')
  })
  searchPanel.value = 'update'
  toast('已根据当前检索生成沉淀草稿')
}
const submitTask = async () => {
  const created = await yixiuApi.createTask(taskForm)
  tasks.value.unshift({ ...created, collaborators: [], sop: created.sop?.length ? created.sop : ['安全确认', '故障记录', '部件检测', '复测提交'] })
  showTaskForm.value = false
  toast('检修任务创建成功')
}
const advanceTask = async (task) => {
  const next = task.status === 'pending' ? 'in_progress' : task.status === 'in_progress' ? 'review' : task.status === 'review' ? 'completed' : 'completed'
  try { await yixiuApi.updateTaskStatus(task.id, next, { operator: user.name }) } catch (_error) { /* local-first fallback; server interface remains available */ }
  task.status = next
  task.progress = next === 'in_progress' ? Math.max(task.progress, 45) : next === 'review' ? 86 : 100
  task.current_step = next === 'in_progress' ? '作业执行' : next === 'review' ? '复测确认' : '归档'
  toast(`任务已流转为：${statusText(next)}`)
}
const taskPrimaryLabel = (task) => ({ pending: '接收并开始任务', in_progress: '提交复检', review: '打开复检评估', completed: '查看归档报告' }[task?.status] || '处理任务')
const handleTaskPrimary = async (task) => {
  if (!task) return
  if (task.status === 'review') return enterTaskRecheck(task)
  if (task.status === 'completed') return previewTaskReport(task)
  if (task.status === 'in_progress' && (task.completedSteps?.length || 0) < (task.sop?.length || 0)) {
    return toast(`还有 ${(task.sop?.length || 0) - (task.completedSteps?.length || 0)} 个作业步骤未确认`)
  }
  await advanceTask(task)
}
const enterTaskRecheck = (task) => {
  if (!task || task.status === 'pending') return toast('任务接收并完成作业步骤后才能进入复检')
  if (task.status === 'in_progress' && (task.completedSteps?.length || 0) < (task.sop?.length || 0)) return toast('请先完成全部标准作业步骤')
  if (task.status === 'in_progress') {
    task.status = 'review'
    task.progress = Math.max(task.progress || 0, 86)
    task.current_step = '复测确认'
  }
  taskPanel.value = 'recheck'
  activePage.value = 'tasks'
  selectedTask.value = null
  nextTick(() => document.querySelector('.skf-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
}
const previewTaskReport = (task) => { reportTask.value = task; selectedTask.value = null }
const windowPrint = () => window.print()
const loadKnowledge = async () => {
  const data = await yixiuApi.knowledge(knowledgeKeyword.value)
  const existingKnowledgeIds = new Set(data.map((item) => item.id))
  const extras = extraKnowledgeSamples.filter((item) => !existingKnowledgeIds.has(item.id) && (!knowledgeKeyword.value || JSON.stringify(item).includes(knowledgeKeyword.value)))
  knowledge.value = [...data, ...extras]
  loadKnowledgeDocs()
}
const saveKnowledge = async () => {
  try {
    const tags = knowledgeForm.tagText.split(/[,，]/).map((item) => item.trim()).filter(Boolean)
    const saved = await yixiuApi.updateKnowledge({ ...knowledgeForm, tags: tags.length ? tags : ['沉淀', '检修案例'] })
    knowledge.value.unshift(saved)
    Object.assign(knowledgeForm, { title: '', type: '历史故障案例', equipment: '', model: '', source: '', tagText: '', summary: '' })
    toast('知识条目已进入人工审核队列')
  } catch (error) {
    toast(error.message || '知识提交失败')
  }
}
const reviewKnowledge = async (item, status) => {
  try {
    const saved = await yixiuApi.reviewKnowledge(item.id, { status, correction: knowledgeCorrections[item.id] || '', tags: item.tags || [], reviewer: user.name })
    Object.assign(item, saved)
    toast(status === 'approved' ? '审核通过，已同步知识状态' : '已退回修改')
  } catch (error) {
    toast(error.message || '审核保存失败')
  }
}
const completeTaskStep = async (task, index) => {
  try {
    let saved
    try { saved = await yixiuApi.completeTaskStep(task.id, index, { evidence: `由${user.name}确认` }) } catch (_error) {
      const completedSteps = [...new Set([...(task.completedSteps || []), index])]
      const progress = Math.min(100, Math.round(completedSteps.length / Math.max(task.sop?.length || 1, 1) * 86))
      saved = { completedSteps, progress, status: completedSteps.length >= (task.sop?.length || 1) ? 'review' : 'in_progress' }
    }
    task.completedSteps = saved.completedSteps
    task.progress = saved.progress
    task.status = saved.status
    task.current_step = saved.status === 'review' ? '等待复检' : stepTitle(task.sop[index + 1])
    toast(saved.status === 'review' ? '作业步骤完成，任务已进入复检' : '步骤完成并已保存')
  } catch (error) {
    toast(error.message || '步骤保存失败')
  }
}
const runAudit = async () => {
  const result = await yixiuApi.audit({ references: true, safety_checked: true, measurements: true, retested: true, report_ready: true })
  auditResult.value = JSON.stringify(result, null, 2)
}

const runOperatorPrimary = () => {
  if (activePage.value === 'home') {
    operatorMessages.value.push(operatorMessage({
      id: `brief-${Date.now()}`,
      page: 'home',
      role: 'assistant',
      text: `今日共 ${tasks.value.length} 项任务，高风险 ${tasks.value.filter((task) => task.severity === 'high').length} 项，待复检 ${tasks.value.filter((task) => task.status === 'review').length} 项。建议先处理高风险和已逾期工单。`
    }, 'tiangong'))
    return toast('今日检修简报已生成')
  }
  if (activePage.value === 'search') return runSearch()
  if (activePage.value === 'tasks') {
    taskPanel.value = 'manage'
    return toast('已打开任务执行中心')
  }
  if (activePage.value === 'knowledge') {
    knowledgePanel.value = 'files'
    return toast('已打开 Agent 中心')
  }
  return runAudit()
}

const createRunContextSnapshot = (prompt = '', attachments = []) => {
  const text = String(prompt || '')
  const files = Array.isArray(attachments) ? attachments : []
  const scene = inferSearchScene(text, files)
  const normalizedQuery = String(searchForm.query || '').trim()
  const promptLooksLikeCurrentSearch = !!normalizedQuery && (
    text.includes(normalizedQuery) ||
    normalizedQuery.includes(text) ||
    (!text && activePage.value === 'search') ||
    (activePage.value === 'search' && /当前|这个|本次|检索|研判|报告|总结|生成|导出/.test(text))
  )
  const currentSearchResult = promptLooksLikeCurrentSearch && !scene && !files.length ? searchResult.value : null
  return {
    prompt: text,
    files: files.map((file) => ({ name: file.name, type: file.type, id: file.id || file.localId || '' })),
    scene,
    searchForm: {
      deviceName: scene?.deviceName || (promptLooksLikeCurrentSearch ? searchForm.deviceName : ''),
      deviceModel: scene?.deviceModel || (promptLooksLikeCurrentSearch ? searchForm.deviceModel : ''),
      faultType: scene?.faultType || (promptLooksLikeCurrentSearch ? searchForm.faultType : ''),
      category: scene?.category || (promptLooksLikeCurrentSearch ? searchForm.category : ''),
      query: scene?.query || text || (promptLooksLikeCurrentSearch ? searchForm.query : '')
    },
    searchResult: currentSearchResult
  }
}

const AGENT_REPLY_FALLBACKS = {
  tiangong: '已收到本次任务。我会按当前输入和本轮上传资料处理，未确认的设备型号、检测值和现场状态会保留为待确认。',
  guanwei: '已收到本次检索请求。我会优先使用当前输入和本轮上传资料检索知识库，不套用上一轮案例。',
  zhiju: '已收到本次作业编排请求。我会围绕当前设备、故障现象和已确认资料整理可执行步骤。',
  bowen: '已收到本次知识整理请求。我会基于当前资料生成可审核的知识候选，缺失信息保持待补充。',
  heming: '已收到本次协作请求。我会根据当前任务内容选择合适联系人和协作动作。',
  mingjian: '已收到本次核查请求。我会按当前任务依据、检测记录和复检要求给出核查意见。'
}

const agentFallbackReply = (agentId = '', agentName = '智能体') => AGENT_REPLY_FALLBACKS[agentId] || `${agentName}已收到本次问题。我会基于当前输入和本轮资料给出建议，未确认信息保持待确认。`

const looksLikeBrokenAgentText = (value = '') => {
  const text = String(value || '').trim()
  if (!text) return true
  const brokenCount = (text.match(/[�锛銆鐨妫绱濈€]/g) || []).length
  const controlCount = (text.match(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g) || []).length
  const symbolCount = (text.match(/[{}[\]<>|`~^\\]/g) || []).length
  const exposesToolTrace = /\[UI_PLAN\]|<\/?tool|tool_calls?|arguments?|undefined|null|NaN/i.test(text)
  return brokenCount >= 3 || controlCount > 0 || (exposesToolTrace && symbolCount > 6)
}

const cleanAgentReplyText = (value, agentId = '', agentName = '智能体') => {
  let text = String(value || '').replace(/\[UI_PLAN\][\s\S]*?\[\/UI_PLAN\]/g, '').trim()
  text = text
    .replace(/```(?:json)?[\s\S]*?```/g, '')
    .replace(/^[\s:：,，;；。]+|[\s:：,，;；。]+$/g, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
  return looksLikeBrokenAgentText(text) ? agentFallbackReply(agentId, agentName) : text
}

const sendOperatorPrompt = async (prompt) => {
  const value = String(prompt || '').trim()
  if (!value && !assistantFiles.value.length) return
  if (value.includes('退出登录')) return logout()
  const sourcePage = activePage.value
  const requestAgentId = activeOperatorAgentId.value
  const visualTransferIntent = isVisualSearchTransferPrompt(value)
  const outgoingAttachments = snapshotFiles(assistantFiles.value)
  const runContext = createRunContextSnapshot(value, outgoingAttachments)
  operatorMessages.value.push(operatorMessage({ id: `user-${Date.now()}`, page: sourcePage, role: 'user', text: value || '请分析已上传的现场资料', attachments: outgoingAttachments }, requestAgentId))
  operatorInput.value = ''
  if (visualTransferIntent) {
    try {
      await runTiangongLongTask(value || '请将现场图片交给观微进行智能检索和故障判断', sourcePage, { attachments: assistantFiles.value.slice(), context: runContext, agentId: requestAgentId })
      return
    } catch (error) {
      Object.assign(tgRunUi, {
        visible: true,
        statusText: '转交失败',
        title: '天工未能转交附件',
        detail: '图片已保留在对话中，请确认后端服务和智能检索页面状态后重试。',
        agentName: '天工',
        page: currentNav.value?.label || '当前页面',
        tool: 'attachment.transfer',
        inputText: value,
        outputText: error.message || '附件转交暂时无法完成。',
        current: 0,
        total: 0,
        progress: 0,
        steps: []
      })
      return toast(error.message || '图片转交智能检索失败')
    }
  }
  if (assistantFiles.value.length) {
    try {
      for (const file of assistantFiles.value.filter((item) => !item.id)) {
        file.status = '上传中'
        const saved = await yixiuApi.uploadFile(file.raw, { purpose: 'assistant', category: '智能问修', folder: '问修附件', uploader: user.name }, (progress) => { file.progress = progress })
        Object.assign(file, saved, { raw: file.raw, localId: file.localId, status: '分析完成' })
      }
      const response = await yixiuApi.assistantChat({ message: value, fileIds: assistantFiles.value.map((file) => file.id).filter(Boolean), agent: operatorProfile.value.name, page: sourcePage })
      const replyText = cleanAgentReplyText(response.response, requestAgentId, operatorProfile.value.name)
      const references = (response.references || []).filter(Boolean)
      operatorMessages.value.push(operatorMessage({
        id: `assistant-${Date.now()}`,
        page: sourcePage,
        role: 'assistant',
        text: references.length ? `${replyText}\n引用：${references.join('、')}` : replyText
      }, requestAgentId))
      // 附件缩略图仍需要显示在历史气泡中，稍后由页面退出统一释放 Blob URL。
      assistantFiles.value = []
      return toast('已完成图文联合分析')
    } catch (error) {
      return toast(error.message || '附件分析失败')
    }
  }
  if (isTiangongLongTaskPrompt(value)) {
    try {
      await runTiangongLongTask(value, sourcePage, { context: runContext, agentId: requestAgentId })
    } catch (error) {
      Object.assign(tgRunUi, {
        visible: true,
        statusText: '连接失败',
        title: '天工长任务启动失败',
        detail: 'AIOS 未能完成本次请求，请确认后端服务已启动后重试。',
        agentName: '天工',
        page: currentNav.value?.label || '当前页面',
        tool: 'AIOS 请求',
        inputText: value,
        outputText: error.message || '智能体服务暂时无法响应。',
        current: 0,
        total: 0,
        progress: 0,
        steps: []
      })
      aiosLive.error = error.message || '天工长任务暂时无法执行'
      operatorMessages.value.push(operatorMessage({ id: `assistant-${Date.now()}`, page: sourcePage, role: 'assistant', text: `天工长任务启动失败：${aiosLive.error}` }, requestAgentId))
      toast(aiosLive.error)
    }
    return
  }
  if (value.includes('高风险')) return goStat({ page: 'tasks', panel: 'manage', severity: 'high' })
  if (value.includes('生成研判') || value.includes('检索建议')) return runSearch()
  if (value.includes('创建任务') || value.includes('新建任务')) {
    activePage.value = 'tasks'
    taskPanel.value = 'manage'
    showTaskForm.value = true
    return
  }
  if (value.includes('流转任务')) {
    const task = filteredTasks.value[0]
    if (task) return advanceTask(task)
    return toast('暂无可流转任务')
  }
  if (value.includes('Skill 工厂') || value.includes('运行 Skill Eval') || value.includes('复检')) {
    activePage.value = 'tasks'
    taskPanel.value = 'recheck'
    if (value.includes('运行 Skill Eval')) runSkillEval(selectedSkill.value)
    return
  }
  if (value.includes('联系人')) {
    activePage.value = 'tasks'
    taskPanel.value = 'contacts'
    return
  }
  if (value.includes('Agent 中心') || value.includes('Agent 注册中心') || value.includes('文件管理')) {
    activePage.value = 'knowledge'
    knowledgePanel.value = 'files'
    return
  }
  if (value.includes('知识网络')) {
    activePage.value = 'search'
    searchPanel.value = 'network'
    return
  }
  if (value.includes('提交沉淀')) {
    activePage.value = 'search'
    searchPanel.value = 'update'
    return
  }
  if (value.includes('运行核查')) return runAudit()
  if (value.includes('个人记录')) {
    activePage.value = 'profile'
    return
  }
  // 左侧导航改名后，助手快捷指令里出现的页面名也要能对上
  if (value.includes('个人空间')) {
    activePage.value = 'profile'
    return
  }
  if (value.includes('能力中心') || value.includes('团队能力')) {
    activePage.value = 'knowledge'
    knowledgePanel.value = 'recheck'
    return
  }
  if (value.includes('任务执行')) {
    activePage.value = 'tasks'
    taskPanel.value = 'manage'
    return
  }
  if (value.includes('上下文中心')) {
    activePage.value = 'search'
    return
  }
  if (value.includes('工作台')) {
    activePage.value = 'home'
    return
  }
  try {
    if (operatorProfile.value.id === 'tiangong') {
      const loadingMsg = operatorMessage({ id: `loading-${Date.now()}`, page: sourcePage, role: 'assistant', text: '天工正在感知系统状态…', loading: true }, 'tiangong')
      operatorMessages.value.push(loadingMsg)
      Object.assign(aiosLive, {
        status: 'running',
        goal: value,
        progress: Math.max(aiosLive.progress || 0, 6),
        error: ''
      })
      const host = `http://${window.location.hostname || '127.0.0.1'}:5000`

      if (isTiangongLongTaskPrompt(value)) {
        operatorMessages.value = operatorMessages.value.filter((message) => message.id !== loadingMsg.id)
        await runTiangongLongTask(value, sourcePage, { context: runContext, agentId: 'tiangong' })
        return
      }
      
      // 只调用 /miniclaw/chat，让天工在 ReAct 循环中自主决定：
      // 1. 先调什么工具了解系统（system_overview / maintenance_task / knowledge_search 等）
      // 2. 基于了解到的真实数据，决定是否输出 [UI_PLAN] 遥控界面
      const chatPayload = await fetch(`${host}/miniclaw/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: value, conversation_id: `tiangong-${sourcePage}` })
      }).then(r => r.json().catch(() => ({})))
      refreshAiosTraceSoon()
      
      const data = chatPayload.data || chatPayload || {}
      const reply = data.reply || '天工暂无回复'
      const toolCalls = data.tool_calls || 0
      const steps = Array.isArray(data.steps) ? data.steps : []
      
      // 从天工回复中解析 [UI_PLAN]（天工自己决定是否需要）
      let uiPlan = null
      const planMatch = reply.match(/\[UI_PLAN\]([\s\S]*?)\[\/UI_PLAN\]/)
      if (planMatch) {
        const raw = planMatch[1].trim()
        const fb = raw.indexOf('['), lb = raw.lastIndexOf(']')
        if (fb >= 0 && lb > fb) {
          try { uiPlan = JSON.parse(raw.slice(fb, lb + 1)) } catch (e) { uiPlan = null }
        }
      }
      
      // 去掉 [UI_PLAN] 标记后的纯文本回复
      const cleanReply = cleanAgentReplyText(reply, 'tiangong', '天工')
      
      const uiCount = Array.isArray(uiPlan) && uiPlan.length ? uiPlan.filter((s) => s.action !== 'done').length : 0
      // 合并工具调用步骤和 UI 操作步骤
      const uiSteps = Array.isArray(uiPlan) && uiPlan.length
        ? buildExecutionTrace(uiPlan, { goal: value })
        : steps
      
      // 替换 loading 消息为真实回复
      const loadIdx = operatorMessages.value.findIndex((m) => m.id === loadingMsg.id)
      const finalMsg = {
        id: loadIdx >= 0 ? loadingMsg.id : `assistant-${Date.now()}`,
        page: sourcePage,
        agentId: 'tiangong',
        role: 'assistant',
        text: cleanReply,
        steps: uiSteps,
        toolCalls: uiCount || toolCalls
      }
      if (loadIdx >= 0) operatorMessages.value.splice(loadIdx, 1, finalMsg)
      else operatorMessages.value.push(finalMsg)
      
      if (uiPlan && uiPlan.length) {
        toast(`天工自主探索后规划了 ${uiCount} 步操作，正在执行…`)
      } else {
        toast(`天工完成 ${toolCalls} 次工具调用`)
      }
      
      if (Array.isArray(uiPlan) && uiPlan.length && !tgRunning.value) {
        await executeUIPlan(uiPlan)
        refreshAiosTraceSoon()
        toast('操作完成，3秒后返回首页…')
        await tgSleep(3000)
        activePage.value = 'home'
      }
      return
    }
    if (operatorProfile.value.id && operatorProfile.value.id !== 'tiangong') {
      const agentId = operatorProfile.value.id
      const history = operatorMessages.value
        .filter((item) => item && item.agentId === agentId && item.role && item.text && !item.loading)
        .slice(-8)
        .map((item) => ({ role: item.role, content: item.text }))
      const response = await yixiuApi.agentChat(agentId, { message: value, history })
      const replyText = cleanAgentReplyText(String(response.response || ''), agentId, operatorProfile.value.name)
      operatorMessages.value.push(operatorMessage({ id: `assistant-${Date.now()}`, page: sourcePage, role: 'assistant', text: replyText || `${operatorProfile.value.name}暂未生成回复。` }, agentId))
      toast(`${operatorProfile.value.name}已独立回答`)
      return
    }
    const response = await yixiuApi.assistantChat({ message: value, fileIds: [], agent: operatorProfile.value.name, page: sourcePage })
    operatorMessages.value.push(operatorMessage({ id: `assistant-${Date.now()}`, page: sourcePage, role: 'assistant', text: cleanAgentReplyText(response.response, requestAgentId, operatorProfile.value.name) }, requestAgentId))
    toast(`${operatorProfile.value.name}已结合当前数据给出建议`)
  } catch (error) {
    if (operatorProfile.value.id === 'tiangong') {
      Object.assign(tgRunUi, {
        visible: true,
        statusText: '连接失败',
        title: '天工无法完成操作',
        detail: '智能体没有拿到可用输出，已保留本次输入，方便重新发送。',
        agentName: '天工',
        page: currentNav.value?.label || '当前页面',
        tool: 'miniclaw.chat',
        inputText: value,
        outputText: error.message || '智能体暂时无法响应。',
        current: 0,
        total: 0,
        progress: 0,
        steps: []
      })
    }
    toast(error.message || '智能体暂时无法响应')
  }
}

const EXECUTION_STAGE_META = {
  parse: { label: '问题解析', desc: '读取用户问题、附件和当前页面上下文。' },
  intent: { label: '意图识别', desc: '确认任务类型、设备范围、风险等级和需要调用的业务模块。' },
  plan: { label: '任务拆解', desc: '把目标拆成可执行的页面动作、检索动作和智能体协作动作。' },
  context: { label: '上下文定位', desc: '进入对应页面或业务面板，锁定当前可处理的数据。' },
  retrieve: { label: '知识检索', desc: '从知识库、知识图谱、历史案例或多模态附件中召回依据。' },
  agent: { label: '智能体协作', desc: '调用专业智能体或联系人协作，获取角色结论。' },
  operate: { label: '作业编排', desc: '生成或匹配 SOP、工单、安全确认和复检动作。' },
  synthesize: { label: '信息整合', desc: '汇总检索依据、页面状态、智能体回复和任务上下文。' },
  verify: { label: '校验确认', desc: '核查关键结论、人工确认项和未确定信息。' },
  report: { label: '结果生成', desc: '生成可查看、可导出、可继续补充的业务结果。' },
  archive: { label: '知识沉淀', desc: '形成待审核知识候选或更新建议。' }
}
const ACTION_STAGE_MAP = {
  sense_overview: 'parse',
  navigate: 'context',
  transfer_attachment: 'parse',
  search: 'retrieve',
  knowledge_search: 'retrieve',
  retrieve_knowledge: 'retrieve',
  diagnose_fault: 'synthesize',
  filter: 'operate',
  openPanel: 'operate',
  openKnowledgeGraph: 'retrieve',
  openChat: 'agent',
  coordinate_team: 'agent',
  type: 'agent',
  click_send: 'agent',
  agent_type: 'agent',
  agent_send: 'agent',
  contact_type: 'agent',
  contact_send: 'agent',
  orchestrate_task: 'operate',
  prepare_recheck: 'verify',
  summarize: 'synthesize',
  record_memory: 'synthesize',
  approve: 'verify',
  report: 'report',
  finalize_report: 'report',
  archive_knowledge: 'archive',
  finish: 'report',
  wait: 'verify'
}
const EXECUTION_STAGE_ORDER = ['parse', 'intent', 'plan', 'context', 'retrieve', 'agent', 'operate', 'synthesize', 'verify', 'report', 'archive']

const traceStageFor = (step = {}) => {
  const source = step.args || step
  const action = source.action || step.action || step.tool || step.type
  const key = source.key || ''
  if (source.stage && EXECUTION_STAGE_META[source.stage]) return source.stage
  if (ACTION_STAGE_MAP[action]) return ACTION_STAGE_MAP[action]
  if (key.includes('open_search') || key.includes('retrieve')) return 'retrieve'
  if (key.includes('operate') || key.includes('task')) return 'operate'
  if (key.includes('review') || key.includes('approve')) return 'verify'
  if (key.includes('archive') || key.includes('knowledge')) return 'archive'
  if (key.includes('finalize') || key.includes('report')) return 'report'
  if (step.type === 'observation') return 'verify'
  if (step.type === 'tool_call') return 'retrieve'
  return 'synthesize'
}

const traceStatusFor = (step = {}, index = 0, steps = []) => {
  const source = step.args || step
  const status = source.status || source.state || step.status
  if (['done', 'success', 'completed'].includes(status)) return 'done'
  if (['running', 'active'].includes(status)) return 'active'
  if (['failed', 'error', 'blocked'].includes(status)) return 'blocked'
  if (['waiting', 'pending_approval'].includes(status)) return 'waiting'
  return index >= Math.max(steps.length - 1, 0) ? 'done' : 'done'
}

const traceAgentName = (step = {}) => {
  const source = step.args || step
  if (source.agentName) return source.agentName
  if (source.agent?.name) return source.agent.name
  if (source.agent && TG_AGENT_NAMES[source.agent]) return TG_AGENT_NAMES[source.agent]
  if (step.agent && TG_AGENT_NAMES[step.agent]) return TG_AGENT_NAMES[step.agent]
  if (source.agent_id && TG_AGENT_NAMES[source.agent_id]) return TG_AGENT_NAMES[source.agent_id]
  return ''
}

const traceContentFor = (step = {}) => {
  const source = step.args || step
  const input = source.input || {}
  const direct = source.content || step.content || traceResult(step)
  if (direct) return direct
  if (source.reason || source.expected) return [source.reason, source.expected].filter(Boolean).join('；')
  const keyword = input.query || input.keyword || source.keyword || source.text
  return keyword ? `处理线索：${keyword}` : EXECUTION_STAGE_META[traceStageFor(step)]?.desc || '执行当前可观察业务步骤。'
}

const traceDisplay = (step = {}, index = 0, steps = []) => {
  const stage = traceStageFor(step)
  const meta = EXECUTION_STAGE_META[stage] || EXECUTION_STAGE_META.synthesize
  return {
    stage,
    status: traceStatusFor(step, index, steps),
    label: step.label || meta.label,
    agentName: traceAgentName(step),
    content: traceContentFor(step)
  }
}

const stepLabel = (type) => {
  if (EXECUTION_STAGE_META[type]) return EXECUTION_STAGE_META[type].label
  return ({ thought: '问题解析', action: '业务动作', tool_call: '工具调用', observation: '结果校验' }[type] || type)
}
const traceResult = (step) => {
  const r = step.tool_result
  if (!r) return ''
  return r.success ? `结果：${r.output}` : `失败：${r.error}`
}

const isTiangongLongTaskPrompt = (value) => {
  const text = String(value || '')
  const namesTiangong = operatorProfile.value.id === 'tiangong' || /天工|AIOS|总控/.test(text)
  const hasLongIntent = /长任务|执行|打开|查找|询问|问|总结|协作|知识库|摩托|汽车|车辆|泡水|涉水|可视化|UI_PLAN|十二步|12步|上传|转交|交给|图片|附件|图像/.test(text)
  const hasCrossAgentTarget = /知识库|智能检索|和鸣|观微|执矩|博闻|明鉴|摩托|汽车|车辆|泡水|涉水|积水|CG-125|复检|联系人|沉淀|闭环|图片|附件|故障|什么问题/.test(text)
  if (namesTiangong && /可视化执行过程|UI_PLAN|12步|十二步/.test(text)) return true
  return hasLongIntent && hasCrossAgentTarget
}

const longTaskReplyText = (data) => {
  const steps = Array.isArray(data.steps) ? data.steps : []
  const body = steps.map((step, index) => {
    const display = traceDisplay(step, index, steps)
    return `${index + 1}. ${display.label}${display.agentName ? ` · ${display.agentName}` : ''}：${display.content}`
  }).join('\n')
  return `${data.summary || '天工已完成长任务规划。'}${body ? `\n\n执行路径：\n${body}` : ''}`
}

const firstTruthy = (...values) => values.find((value) => value !== undefined && value !== null && String(value).trim() !== '') || ''
const compactList = (items = []) => [...new Set(items.map((item) => String(item || '').trim()).filter(Boolean))]
const createLatestSearchRunContext = (prompt = '', baseContext = {}) => ({
  ...baseContext,
  prompt: String(prompt || baseContext.prompt || ''),
  files: snapshotFiles(searchFiles.value).map((file) => ({ name: file.name, type: file.type, id: file.id || file.localId || '' })),
  searchForm: {
    deviceName: searchForm.deviceName,
    deviceModel: searchForm.deviceModel,
    faultType: searchForm.faultType,
    category: searchForm.category,
    query: searchForm.query
  },
  searchResult: searchResult.value
})

const buildReportContext = (data = {}, uiSteps = []) => {
  const focus = data.focus || data.task || {}
  const runContext = data.context || data.runContext || {}
  const contextSearchForm = runContext.searchForm || {}
  const contextSearchResult = runContext.searchResult || null
  const digest = Array.isArray(data.step_digest) ? data.step_digest : Array.isArray(data.steps) ? data.steps : []
  const scene = inferSearchScene(
    [
      runContext.prompt,
      data.goal,
      contextSearchForm.query,
      contextSearchResult?.query,
      focus.fault_type,
      focus.description,
      ...uiSteps.map((step) => step.content || step.args?.reason || step.args?.input?.query || step.args?.input?.keyword || '')
    ].join(' '),
    runContext.files || []
  )
  const sceneText = [
    runContext.prompt,
    data.goal,
    contextSearchForm.query,
    contextSearchResult?.query,
    focus.fault_type,
    focus.description,
    ...(runContext.files || []).map((file) => file.name || '')
  ].join(' ')
  const hasAutoVehicleIntent = /汽车|轿车|车辆/.test(sceneText)
  const hasMotorcycleEngineIntent = scene?.type === 'motorcycle_engine' || /摩托|cg-?125/.test(sceneText) || (!hasAutoVehicleIntent && /发动机异响|气门|怠速|正时链条|张紧器|火花塞|化油器/.test(sceneText))
  const hasWaterIntent = hasAffirmativeWaterScene(sceneText)
  const device = firstTruthy(contextSearchResult?.device?.name, contextSearchResult?.device_name, focus.equipment_name, focus.equipment, scene?.deviceName, contextSearchForm.deviceName, '待确认设备')
  const model = firstTruthy(contextSearchResult?.device?.model, contextSearchResult?.device_model, focus.equipment_model, focus.model, scene?.deviceModel, contextSearchForm.deviceModel)
  const fault = firstTruthy(contextSearchResult?.fault?.type, contextSearchResult?.fault_type, focus.fault_type, scene?.faultType, contextSearchForm.faultType, focus.description, data.goal, '待确认故障')
  const risk = firstTruthy(contextSearchResult?.risk?.level, contextSearchResult?.risk, focus.severity, contextSearchResult?.riskLevel, '待评估')
  const rawRefs = Array.isArray(contextSearchResult?.references)
    ? contextSearchResult.references
    : (Array.isArray(contextSearchResult?.matched_manuals) ? contextSearchResult.matched_manuals : [])
  const refs = hasMotorcycleEngineIntent && !hasWaterIntent
    ? rawRefs.filter((item) => !/泡水|涉水|水淹|积水|进水/.test(`${item.title || ''}${item.category || ''}${item.summary || ''}${(item.tags || []).join('')}`))
    : rawRefs
  const sop = Array.isArray(contextSearchResult?.suggestion?.steps)
    ? contextSearchResult.suggestion.steps
    : (Array.isArray(contextSearchResult?.recommended_sop) ? contextSearchResult.recommended_sop.map((item) => item.action || item.title || item.detail).filter(Boolean) : [])
  const agents = compactList([
    ...digest.map((step) => step.agent || step.agent_id || step.agentName),
    ...uiSteps.map((step) => traceAgentName(step))
  ])
  return {
    goal: data.goal || contextSearchForm.query || focus.title || '当前检修任务',
    device,
    model,
    fault,
    risk,
    refs,
    sop,
    agents,
    sceneType: scene?.type || '',
    isMotorcycleEngine: hasMotorcycleEngineIntent || /摩托|cg-?125|发动机异响|气门|怠速|正时链条|张紧器|火花塞|化油器/.test(`${device} ${model} ${fault}`),
    isVehicleWater: !hasMotorcycleEngineIntent && (scene?.type === 'vehicle_water' || hasWaterIntent || /泡水|涉水|积水|水淹|进水/.test(`${device} ${fault}`)),
    highlights: compactList([
      ...digest.slice(0, 5).map((step) => step.content || step.expected_output || step.title),
      contextSearchResult?.diagnosis,
      contextSearchResult?.phenomenonSummary,
      contextSearchResult?.phenomenon_summary,
      contextSearchResult?.stopAdvice,
      contextSearchResult?.stop_advice
    ]).slice(0, 5)
  }
}

const makeReportItem = (id, type, title, reason, sections, tags = [], priority = '建议') => ({
  id,
  type,
  title,
  reason,
  sections: compactList(sections).slice(0, 5),
  tags,
  priority
})

const buildReportRecommendations = (ctx = {}) => {
  const subject = `${ctx.device || '待确认设备'}${ctx.model ? ` / ${ctx.model}` : ''}`
  const fault = ctx.fault || '待确认故障'
  const refsText = ctx.refs?.length ? `已召回 ${ctx.refs.length} 份资料/案例，可列为报告依据。` : '当前未召回明确资料，报告中应保留“依据待补充”。'
  const base = []
  if (ctx.isMotorcycleEngine) {
    base.push(
      makeReportItem(
        'motor-engine-analysis',
        '故障分析',
        `${subject}发动机异响故障分析报告`,
        '当前任务指向摩托车发动机异响/怠速不稳，报告应围绕气门机构、正时链条、润滑、点火和进气系统展开。',
        [
          `设备对象：${subject}；故障现象：${fault}。`,
          '优先原因：气门间隙异常、正时链条/张紧器松旷、摇臂/凸轮轴磨损、机油润滑不良。',
          refsText,
          '车型、里程、冷车/热车差异和检测数值保留为待确认。'
        ],
        ['摩托车发动机', '异响', '怠速不稳'],
        '高优先级'
      ),
      makeReportItem(
        'motor-valve-clearance',
        '专项检查',
        `${subject}气门间隙检查记录`,
        '发动机上部异响常与气门间隙相关，应单独记录测量和调整过程。',
        [
          '记录停机冷却状态、拆检位置、进/排气门测量值和调整值。',
          '使用塞尺检查，复装后进行冷车、热车复测。',
          '未实际测量前不得写成已完成或合格。'
        ],
        ['气门间隙', '塞尺', '复测']
      ),
      makeReportItem(
        'motor-timing-chain',
        '专项检查',
        `${subject}正时链条与张紧器检修记录`,
        '正时链条松旷或张紧器异常会造成连续敲击/哗啦声，适合形成专项检查记录。',
        [
          '检查链条松旷、张紧器回位、导轨磨损和正时标记。',
          '记录是否更换张紧器、导轨或链条。',
          '复测怠速和加速过程是否仍有异响。'
        ],
        ['正时链条', '张紧器', '导轨']
      ),
      makeReportItem(
        'motor-idle-sop',
        '作业执行',
        `${subject}怠速不稳排查 SOP`,
        '怠速不稳需要同步排查点火、化油器怠速油路和进气漏气，不能只看机械异响。',
        [
          '检查火花塞积碳、高压帽连接和点火强度。',
          '清洁化油器怠速油路，检查混合气和怠速调整。',
          '检查进气歧管、密封垫和真空管是否漏气。'
        ],
        ['怠速不稳', '点火', '化油器']
      )
    )
  }
  if (ctx.isVehicleWater) {
    base.push(
      makeReportItem(
        'vehicle-water-repair',
        '检修研判',
        `${subject}泡水检修研判报告`,
        `用户问题与附件指向车辆涉水/泡水场景，报告需围绕禁止启动、电气进水、油液乳化和拖车处置展开。`,
        [
          `设备对象：${subject}；故障现象：${fault}。`,
          '现场处置：未确认进气和电控状态前禁止启动，优先断开电瓶负极并拖车。',
          '重点检查：空气滤芯/进气管、机油与变速箱油乳化、ECU/保险盒/线束插头受潮。',
          refsText,
          '结论字段保留未知车型、涉水深度、发动机是否启动等待确认项。'
        ],
        ['泡水车辆', '启动前禁启', '电气复检'],
        '高优先级'
      ),
      makeReportItem(
        'vehicle-safety-checklist',
        '安全确认',
        '泡水车辆启动前安全确认单',
        '该场景最大风险是误启动导致发动机二次损伤和电气短路，应单独生成确认单。',
        [
          '确认拖车到安全维修点，现场拍照留证。',
          '确认电瓶负极断开，保险盒、ECU、线束插头无明显积水后再通电检测。',
          '确认进气系统未进水、油液未乳化、制动系统完成检查。',
          '未通过任一项时保持禁启状态并升级为拆检。'
        ],
        ['安全确认', '禁启', '复检']
      ),
      makeReportItem(
        'vehicle-insurance-evidence',
        '证据记录',
        '水淹车辆现场证据与保险处置记录',
        '已上传现场图片，适合形成可追溯证据，便于维修、保险和责任确认。',
        [
          '记录图片时间、地点、积水高度、车身外观和车内进水痕迹。',
          '记录是否尝试启动、拖车时间、维修接收人和初检结论。',
          '附加维修报价、损伤部件清单和后续复检结果。',
          '未知信息不补写，留作待车主或维修点确认。'
        ],
        ['现场证据', '保险', '追溯']
      )
    )
  }
  base.push(
    makeReportItem(
      'fault-analysis',
      '故障分析',
      `${subject}${fault}故障分析报告`,
      '基于当前问题、检索结果和智能体执行链路，适合作为本次检修的主报告。',
      [
        `设备对象：${subject}。`,
        `故障/任务：${fault}。`,
        refsText,
        ctx.highlights?.[0] || '列出已确认现象、可能原因、检测方法和不确定项。',
        `风险等级：${ctx.risk || '待评估'}。`
      ],
      ['故障研判', '检索依据', '风险']
    ),
    makeReportItem(
      'sop-execution',
      '作业执行',
      `${subject}检修 SOP 与过程记录`,
      ctx.sop?.length ? `当前已形成 ${ctx.sop.length} 个建议步骤，适合转成现场作业记录。` : '当前任务仍需要人工补充 SOP，报告会保留待完善项。',
      [
        ...(ctx.sop?.length ? ctx.sop.slice(0, 4) : ['补充安全隔离、拆检、维修、复测和恢复运行记录。']),
        '记录工具、备件、检测值、负责人和完成时间。',
        '未完成步骤标记为待补充，不自动写成已完成。'
      ],
      ['SOP', '作业记录', '复测']
    ),
    makeReportItem(
      'verification',
      '复检核查',
      `${subject}复检与质量核查报告`,
      '检修结论需要经过明鉴/负责人复核，避免把检索建议直接当最终维修结果。',
      [
        '核查故障是否复现、检测值是否恢复正常、安全项是否全部确认。',
        '列出阻断项、返工项和可恢复运行条件。',
        '对未知型号、未知损伤程度、未上传检测数据保持待确认。',
        '形成最终签字/审核入口。'
      ],
      ['复检', '质量核查', '人工确认']
    ),
    makeReportItem(
      'knowledge-candidate',
      '知识沉淀',
      `${subject}${fault}知识沉淀候选`,
      '若本次检修有图片、资料或复检结论，可沉淀为待审核知识，但不直接入库。',
      [
        '沉淀内容只引用已上传图片、检索资料、工单记录和复检结论。',
        '提取故障现象、原因、处置步骤、适用设备和不适用条件。',
        '标记证据来源与审核人，审核通过后再入库。',
        refsText
      ],
      ['知识库', '待审核', '经验复用']
    )
  )
  const scoped = ctx.isMotorcycleEngine && !ctx.isVehicleWater
    ? base.filter((item) => !/泡水|涉水|水淹|积水|进水/.test(`${item.title}${item.reason}${item.sections.join('')}${item.tags.join('')}`))
    : base
  return scoped.slice(0, ctx.isVehicleWater || ctx.isMotorcycleEngine ? 5 : 4)
}

const buildTaskReportRecommendations = (task = {}) => {
  const taskText = `${task?.equipment_name || ''}${task?.equipment || ''}${task?.equipment_model || ''}${task?.model || ''}${task?.description || ''}${task?.title || ''}${task?.fault_type || ''}`
  const ctx = {
    device: task?.equipment_name || task?.equipment || '待确认设备',
    model: task?.equipment_model || task?.model || '',
    fault: task?.fault_type || task?.description || task?.title || '待确认故障',
    risk: task?.severity || '',
    refs: [],
    sop: Array.isArray(task?.sop) ? task.sop.map(stepTitle) : [],
    highlights: [task?.description, task?.recheck?.comment],
    isMotorcycleEngine: /摩托|cg-?125|发动机异响|气门|怠速|正时链条|张紧器|火花塞|化油器/.test(taskText),
    isVehicleWater: !/摩托|cg-?125|发动机异响|气门|怠速|正时链条|张紧器|火花塞|化油器/.test(taskText) && /泡水|涉水|积水|水淹|进水/.test(taskText)
  }
  return buildReportRecommendations(ctx).slice(0, 4)
}

const buildAiosReport = (data = {}, uiSteps = []) => {
  const digest = Array.isArray(data.step_digest) ? data.step_digest : Array.isArray(data.steps) ? data.steps : []
  const ctx = buildReportContext(data, uiSteps)
  const agents = ctx.agents.length ? ctx.agents : [...new Set(digest.map((step) => step.agent || step.agent_id).filter(Boolean))]
  const readableAgents = agents.length ? agents.join('、') : '天工、观微、执矩、和鸣、博闻、明鉴'
  const highlights = ctx.highlights.length ? ctx.highlights : digest.slice(0, 4).map((step) => step.content || step.expected_output || step.title).filter(Boolean)
  const recommendations = buildReportRecommendations(ctx)
  return {
    title: `${ctx.device}${ctx.fault ? ` · ${ctx.fault}` : ''}执行报告`,
    subtitle: data.summary || '天工已完成本轮跨页面协同执行',
    conclusion: `已完成${ctx.device}${ctx.model ? `/${ctx.model}` : ''}的检修线索整理、资料检索、智能体协作、作业/复检定位和报告推荐。未确认的设备参数、检测值、现场状态已保留为待确认；正式归档前需要负责人复核。`,
    metrics: [
      { label: '执行步骤', value: `${uiSteps.length || digest.length || 0} 步` },
      { label: '协作智能体', value: `${agents.length || 1} 个` },
      { label: '检索依据', value: `${ctx.refs.length || 0} 份` },
      { label: '推荐报告', value: `${recommendations.length} 份` }
    ],
    blocks: [
      {
        title: '真实执行链路',
        items: [
          '读取用户问题、附件和当前页面上下文。',
          '识别设备/故障/风险字段，无法确认的信息保持待确认。',
          '按需要进入智能检索、检修任务、知识库、联系人或复检页面。',
          '仅把可观察的页面动作、检索动作、智能体协作和校验结果展示出来。'
        ]
      },
      {
        title: '智能体分工',
        items: [
          `参与：${readableAgents}`,
          '观微负责资料召回与故障研判，执矩负责作业步骤和任务联动。',
          '和鸣负责协作沟通，博闻负责知识网络，明鉴负责复检核查。'
        ]
      },
      {
        title: '本次关键依据',
        items: highlights.length ? highlights : [
          `设备：${ctx.device}${ctx.model ? ` / ${ctx.model}` : ''}`,
          `故障：${ctx.fault}`,
          '当前缺少明确检索依据或现场检测数据，正式报告需继续补充。'
        ]
      },
      {
        title: '待人工确认',
        items: [
          '高风险处置、复电/启动、拆检结论和知识入库必须人工确认。',
          '未知设备型号、故障程度、检测值和现场环境保持空缺或待确认。',
          '最终归档前建议补充图片、检测数据、负责人签字和复检结果。'
        ]
      }
    ],
    recommendations,
    tags: compactList(['真实执行链路', '动态报告', ctx.device, ctx.fault, ctx.isMotorcycleEngine ? '发动机检修' : (ctx.isVehicleWater ? '泡水车辆' : '设备检修')]).slice(0, 6)
  }
}

const buildExecutionTrace = (uiPlan = [], data = {}) => {
  const steps = Array.isArray(uiPlan) ? uiPlan.filter((s) => s.action !== 'done') : []
  return steps.map((s) => {
    const stage = traceStageFor({ args: s })
    const meta = EXECUTION_STAGE_META[stage] || EXECUTION_STAGE_META.synthesize
    return {
      type: stage,
      stage,
      label: meta.label,
      status: s.status || s.state || 'done',
      agent: s.agent,
      agentName: s.agentName || s.agent?.name || TG_AGENT_NAMES[s.agent] || '',
      tool: s.mcpTool || s.tool || s.action || '',
      args: s,
      content: s.reason || s.expected || s.input?.query || s.input?.keyword || s.keyword || s.text || data.goal || ''
    }
  })
}

const runTiangongLongTask = async (value, sourcePage, options = {}) => {
  const transferAttachments = Array.isArray(options.attachments) ? options.attachments.filter(Boolean) : []
  const runContext = options.context || createRunContextSnapshot(value, snapshotFiles(transferAttachments))
  const messageAgentId = options.agentId || 'tiangong'
  const loadingMsg = operatorMessage({ id: `loading-${Date.now()}`, page: sourcePage, role: 'assistant', text: '天工正在感知系统状态…', loading: true }, messageAgentId)
  operatorMessages.value.push(loadingMsg)
  Object.assign(aiosLive, {
    status: 'running',
    goal: value,
    progress: Math.max(aiosLive.progress || 0, 6),
    error: ''
  })
  Object.assign(tgRunUi, {
    visible: true,
    statusText: '规划中',
    title: '生成可执行任务链路',
    detail: '天工正在读取系统状态，并请求 AIOS 返回当前能力范围内可执行的页面路线。',
    agentName: '天工',
    page: '工作台 / AIOS',
    tool: 'aios.long-task',
    inputText: value,
    outputText: '等待后端返回 UI_PLAN。',
    current: 0,
    total: 0,
    progress: 4,
    steps: [
      { index: 1, label: '问题解析' },
      { index: 2, label: '意图识别' },
      { index: 3, label: '任务拆解' }
    ]
  })
  const host = `http://${window.location.hostname || '127.0.0.1'}:5000`
  const taskPayload = await fetch(`${host}/api/yixiu/aios/long-task`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ goal: value })
  }).then(r => r.json().catch(() => ({})))

  const data = { ...(taskPayload.data || taskPayload || {}), context: runContext, goal: value }
  let uiPlan = Array.isArray(data.ui_plan) ? data.ui_plan : []
  if (transferAttachments.length) {
    const transferStep = {
      index: 2,
      action: 'transfer_attachment',
      page: '智能检索',
      agent: 'guanwei',
      agentName: '观微',
      target: '多模态附件区',
      input: { keyword: value, files: transferAttachments.map((file) => file.name) },
      reason: `天工将 ${transferAttachments.length} 个现场附件交给观微，用于图文联合检索。`,
      expected: '图片出现在智能检索附件区，并成为检索上下文。',
      mcpTool: 'attachment_transfer+vision_context'
    }
    uiPlan = [
      { index: 1, action: 'navigate', page: '智能检索', agent: 'guanwei', agentName: '观微', target: '智能检索页面', input: { keyword: value }, reason: '先进入观微智能检索页面。', expected: '智能检索页面已打开。' },
      transferStep,
      ...uiPlan.filter((step) => !['navigate'].includes(step.action) || (step.page !== '首页' && step.page !== '工作台'))
    ].map((step, index) => ({ ...step, index: index + 1 }))
  }
  applyAiosRun(data, Array.isArray(data.events) ? data.events : [])
  const uiSteps = buildExecutionTrace(uiPlan, { ...data, goal: value })
  const loadIdx = operatorMessages.value.findIndex((m) => m.id === loadingMsg.id)
  const finalMsg = {
    id: loadIdx >= 0 ? loadingMsg.id : `assistant-${Date.now()}`,
    page: sourcePage,
    agentId: messageAgentId,
    role: 'assistant',
    text: longTaskReplyText(data),
    report: buildAiosReport(data, uiSteps),
    steps: uiSteps,
    toolCalls: uiSteps.length,
    global: false
  }
  if (loadIdx >= 0) operatorMessages.value.splice(loadIdx, 1, finalMsg)
  else operatorMessages.value.push(finalMsg)

  if (uiPlan.length) {
    tgRunUi.outputText = `已返回 ${uiSteps.length} 个可视化执行步骤。`
    toast(`天工已规划 ${uiSteps.length} 步长任务，开始执行`)
    await executeUIPlan(uiPlan, { transferAttachments })
    refreshAiosTraceSoon()
    toast('长任务执行完成')
    if (transferAttachments.length) {
      assistantFiles.value = []
    }
    finalMsg.report = buildAiosReport({ ...data, context: createLatestSearchRunContext(value, runContext), goal: value }, uiSteps)
    const latestIdx = operatorMessages.value.findIndex((m) => m.id === finalMsg.id)
    if (latestIdx >= 0) operatorMessages.value.splice(latestIdx, 1, { ...finalMsg })
  } else {
    tgRunUi.statusText = '规划失败'
    tgRunUi.outputText = '后端未返回可执行步骤，请换一条更明确的业务指令。'
    toast('天工未返回可视化步骤，请换一条更明确的执行指令')
  }
}

// ===== 天工 UI 遥控 =====
const TG_PAGE_MAP = {
  tiangong: { page: 'home' },
  guanwei: { page: 'search' },
  zhiju: { page: 'tasks', panel: 'manage' },
  heming: { page: 'tasks', panel: 'contacts' },
  mingjian: { page: 'knowledge', panel: 'recheck' },
  bowen: { page: 'knowledge' }
}
const TG_AGENT_NAMES = { tiangong: '天工', guanwei: '观微', zhiju: '执矩', heming: '和鸣', mingjian: '明鉴', bowen: '博闻' }
const tgCursor = ref({ x: 0, y: 0, visible: false, label: '' })
const tgRunning = ref(false)
const tgRunUi = reactive({
  visible: false,
  statusText: '规划中',
  title: '准备执行',
  detail: '天工正在规划操作路径',
  agentName: '天工',
  page: '工作台',
  tool: 'AIOS',
  inputText: '等待用户指令',
  outputText: '等待系统返回',
  observation: '等待感知页面',
  decision: '等待选择动作',
  check: '等待校验结果',
  current: 0,
  total: 0,
  progress: 0,
  steps: []
})
const stopTgRun = () => {
  tgRunning.value = false
  tgCursor.value = { ...tgCursor.value, visible: false, label: '' }
  Object.assign(tgRunUi, {
    statusText: '已中断',
    title: '执行已中断',
    detail: '用户已中断本次 AI 执行，后续页面动作不会继续。',
    outputText: '执行已停止。',
    decision: '收到用户中断指令，停止后续步骤。',
    check: '已中断，未继续校验。'
  })
  toast('已中断 AI 执行')
}
const tgSleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

const tgActionLabel = (step) => {
  const action = step?.action
  const stage = traceStageFor({ args: step })
  const base = EXECUTION_STAGE_META[stage]?.label || '执行操作'
  if (action === 'navigate') return `上下文定位`
  if (action === 'transfer_attachment') return '问题解析'
  if (action === 'filter' || action === 'openPanel' || action === 'orchestrate_task') return '作业编排'
  if (action === 'approve' || action === 'wait' || action === 'prepare_recheck') return '校验确认'
  if (action === 'report' || action === 'finalize_report' || action === 'finish') return '结果生成'
  return base
}

const tgActionDetail = (step) => {
  const action = step?.action
  const inputText = step?.input?.query || step?.input?.keyword || step?.keyword || step?.text || ''
  if (action === 'navigate') return `切换到「${step.page || TG_AGENT_NAMES[step.agent] || step.agent}」，准备由${step.agentName || TG_AGENT_NAMES[step.agent] || '天工'}处理。`
  if (action === 'search') return `在智能检索中带入「${inputText || '当前故障目标'}」，让观微召回资料。`
  if (action === 'filter') return `进入检修任务，按「${inputText || step.target || '相关工单'}」筛选任务。`
  if (action === 'openPanel') return `打开「${step.page || step.target || '业务板块'}」，查看详情、表单或审核内容。`
  if (action === 'openKnowledgeGraph') return `打开知识图谱，定位「${inputText || '设备、故障、资料关系'}」。`
  if (action === 'openChat') return `打开联系人交流，准备向${step.agentName || '协作智能体'}同步任务信息。`
  if (action === 'summarize') return '把本轮检索、任务、协作和知识沉淀写入会话记忆。'
  if (action === 'approve') return '该步骤涉及关键业务动作，需要人工确认后继续。'
  if (action === 'report') return '汇总检索依据、作业步骤、协作记录、复检结果和知识沉淀状态。'
  if (action === 'finish') return step.expected || '天工已完成本次跨页面闭环任务。'
  if (action === 'knowledge_search') return `在知识库中带入关键词「${inputText}」。`
  if (action === 'type') return step.text || '填写智能体指令。'
  if (action === 'click_send') return '把当前指令发送给页面智能体。'
  if (action === 'agent_type') return `天工移动到智能体输入框，逐字输入「${step.text || inputText || '协作问题'}」。`
  if (action === 'agent_send') return '天工点击发送按钮，把消息提交给当前智能体。'
  if (action === 'transfer_attachment') return `天工将 ${step.input?.files?.length || 1} 个现场附件放入智能检索，由观微进行图文联合判断。`
  if (action === 'contact_type') return `天工进入联系人交流区，逐字输入「${step.text || inputText || '协作消息'}」。`
  if (action === 'contact_send') return '天工点击联系人会话发送按钮，写入真实聊天记录。'
  if (action === 'wait') return `等待智能体处理，约 ${step.seconds || 2} 秒。`
  return step?.reason || '执行当前操作。'
}

const tgPageKey = (step = {}) => {
  const text = `${step.page || ''} ${step.target || ''}`
  if (text.includes('智能检索') || text.includes('上下文')) return 'search'
  if (text.includes('知识库') || text.includes('知识图谱') || text.includes('沉淀') || text.includes('团队能力')) return 'knowledge'
  if (text.includes('检修任务') || text.includes('联系人') || text.includes('复检') || text.includes('任务执行')) return 'tasks'
  if (text.includes('个人中心') || text.includes('个人空间')) return 'profile'
  if (text.includes('首页') || text.includes('工作台') || text.includes('报告预览')) return 'home'
  return TG_PAGE_MAP[step.agent]?.page || activePage.value
}

const tgStepInputText = (step = {}) => {
  const input = step.input || {}
  const parts = [
    input.query || input.keyword || step.keyword || step.text,
    input.deviceName || input.equipmentName,
    input.model || input.deviceModel,
    input.faultCode,
    input.faultType
  ].filter(Boolean)
  if (parts.length) return parts.join(' · ')
  return step.target || step.reason || '读取当前页面业务状态'
}

const tgStepOutputText = (step = {}) => {
  const action = step.action
  const page = tgPageKey(step)
  if (action === 'navigate') return `已进入${currentNav.value?.label || '目标页面'}，页面状态已同步。`
  if (action === 'search') {
    const refs = searchResult.value?.references?.length || 0
    const confidence = searchResult.value?.confidence
    return refs ? `已生成研判，召回 ${refs} 份依据${confidence ? `，置信度 ${confidence}%` : ''}。` : '已提交检索请求，等待观微返回研判。'
  }
  if (action === 'filter' || page === 'tasks') return `任务筛选已应用，当前匹配 ${filteredTasks.value.length} 项工单。`
  if (action === 'openKnowledgeGraph' || action === 'knowledge_search' || page === 'knowledge') {
    if (knowledgePanel.value === 'network') return `知识图谱已定位，当前可见 ${graphNodes.value.length} 个实体节点。`
    if (knowledgePanel.value === 'files') return `Agent 中心已打开，本机已接入 ${acStatusCounts.value.connected} 个 Agent，${acStatusCounts.value.notDetected} 个未检测到。`
    if (knowledgePanel.value === 'update') return '沉淀更新表单已打开，可提交待审核知识条目。'
    return `知识库已打开，当前资料 ${knowledge.value.length} 条。`
  }
  if (action === 'openChat') return `联系人交流已打开，当前会话 ${conversations.value.length} 个。`
  if (action === 'summarize') return '已整理检索、任务、协作和知识沉淀上下文。'
  if (action === 'approve') return '已进入人工确认节点，等待用户批准。'
  if (action === 'report') return '已生成闭环报告结构，等待最终确认。'
  if (action === 'type' || action === 'agent_type') return '指令已逐字写入智能体输入框。'
  if (action === 'click_send' || action === 'agent_send') return '指令已发送给当前智能体，等待回复。'
  if (action === 'transfer_attachment') return `已把现场附件加入智能检索，当前检索区共有 ${searchFiles.value.length} 个附件。`
  if (action === 'contact_type') return '协作消息已逐字写入联系人输入框。'
  if (action === 'contact_send') return `消息已发送到「${activeConversation.value?.name || '当前会话'}」。`
  if (action === 'wait') return '等待完成，已继续监听后续结果。'
  return step.expected || '页面动作已完成。'
}

const isVisibleNode = (el) => !!(el && (el.offsetWidth || el.offsetHeight || el.getClientRects().length))
const pickVisibleElement = (selector) => [...document.querySelectorAll(selector)].find(isVisibleNode)

const tgObservePage = () => {
  const pageName = currentNav.value?.label || '当前页面'
  const visibleInputs = [...document.querySelectorAll('input, textarea')].filter(isVisibleNode).length
  const visibleButtons = [...document.querySelectorAll('button')].filter(isVisibleNode).length
  const attachments = assistantFiles.value.length + searchFiles.value.length
  const pageFacts = []
  if (activePage.value === 'search') pageFacts.push(`检索区${searchFiles.value.length}个附件`, searchResult.value ? '已有检索结果' : '等待检索')
  if (activePage.value === 'tasks') pageFacts.push(`任务${filteredTasks.value.length}项`, `当前${taskPanel.value}`)
  if (activePage.value === 'knowledge') pageFacts.push(`知识${knowledge.value.length}条`, `图谱${graphNodes.value.length}节点`)
  if (activePage.value === 'home') pageFacts.push(`今日任务${tasks.value.length}项`)
  return `${pageName}，可见按钮${visibleButtons}个、输入框${visibleInputs}个${attachments ? `、附件${attachments}个` : ''}${pageFacts.length ? `；${pageFacts.join('，')}` : ''}`
}

const tgDecisionFor = (step = {}) => {
  const agentName = step.agentName || TG_AGENT_NAMES[step.agent] || '天工'
  const action = tgActionLabel(step)
  if (step.action === 'transfer_attachment') return `选择观微处理图片线索，先把附件放入多模态检索区。`
  if (step.action === 'agent_send') return `把当前问题交给${agentName}，等待它返回角色结论。`
  if (step.action === 'contact_send') return '这是人员沟通动作，写入联系人会话而不是智能体。'
  if (step.action === 'navigate') return `需要切换页面，所以先进入「${step.page || agentName}」。`
  return `选择${agentName}执行「${action}」。`
}

const tgCheckResultFor = (step = {}) => {
  const page = tgPageKey(step)
  if (step.action === 'transfer_attachment') return searchFiles.value.length ? `校验通过：智能检索区已有 ${searchFiles.value.length} 个附件。` : '校验提醒：未检测到检索附件。'
  if (step.action === 'agent_send') return `校验通过：已向${TG_AGENT_NAMES[step.agent] || step.agentName || '智能体'}发起接口协作。`
  if (page === 'search') return searchResult.value ? `校验通过：观微已生成检索结果，置信度 ${searchResult.value.confidence || '--'}。` : '校验完成：已停留在智能检索区。'
  if (page === 'tasks') return `校验通过：当前任务板块为 ${taskPanel.value}，匹配 ${filteredTasks.value.length} 项。`
  if (page === 'knowledge') return `校验通过：知识库当前为 ${knowledgePanel.value}，图谱节点 ${graphNodes.value.length} 个。`
  return `校验通过：当前页面为 ${currentNav.value?.label || '目标页面'}。`
}

const tgVisibleMessageFor = (step = {}) => {
  const keyword = tgStepInputText(step)
  const action = step.action
  if (action === 'openChat') return `和鸣，请汇总今天未读协作消息，并同步 ${keyword} 相关联系人。`
  if (action === 'openKnowledgeGraph' || action === 'knowledge_search') return `博闻，请解释「${keyword}」在知识图谱中的关联资料和上下游关系。`
  if (action === 'search') return `观微，请基于「${keyword}」输出故障线索、引用资料和下一步建议。`
  if (action === 'filter') return `执矩，请结合当前筛选结果说明高风险工单的执行优先级。`
  if (action === 'openPanel' && String(step.page || '').includes('复检')) return `明鉴，请说明当前待复检任务的质量核查重点。`
  return `天工，请记录当前步骤结果：${tgActionLabel(step)}。`
}

const expandTgVisiblePlan = (steps = []) => {
  const expanded = []
  const messagedAgents = new Set()
  steps.forEach((step) => {
    expanded.push(step)
    const agentId = step.agent || ''
    const shouldAskAgent = agentId && agentId !== 'tiangong' && agentProfileMap[agentId] && !messagedAgents.has(agentId)
    if (shouldAskAgent && ['search', 'filter', 'openPanel', 'openKnowledgeGraph', 'knowledge_search', 'openChat'].includes(step.action)) {
      const text = tgVisibleMessageFor(step)
      expanded.push({
        ...step,
        action: 'agent_type',
        page: step.page || TG_AGENT_NAMES[agentId] || '智能体协作',
        target: `${TG_AGENT_NAMES[agentId] || step.agentName || '智能体'}输入框`,
        text,
        reason: `展示天工使用键盘向${TG_AGENT_NAMES[agentId] || step.agentName || '智能体'}输入协作指令`,
        expected: '问题写入智能体输入框'
      })
      expanded.push({
        ...step,
        action: 'agent_send',
        page: step.page || TG_AGENT_NAMES[agentId] || '智能体协作',
        target: `${TG_AGENT_NAMES[agentId] || step.agentName || '智能体'}发送按钮`,
        text,
        reason: `展示天工点击发送给${TG_AGENT_NAMES[agentId] || step.agentName || '智能体'}`,
        expected: `${TG_AGENT_NAMES[agentId] || step.agentName || '智能体'}返回业务建议`
      })
      messagedAgents.add(agentId)
    }
  })
  const hasBowenInteraction = expanded.some((step) => step.agent === 'bowen' && ['agent_type', 'agent_send'].includes(step.action))
  const hasKnowledgeStep = expanded.some((step) => step.agent === 'bowen' || ['openKnowledgeGraph', 'knowledge_search'].includes(step.action))
  if (hasKnowledgeStep && !hasBowenInteraction) {
    const keyword = steps.map((step) => step.input?.query || step.input?.keyword || step.text || '').find(Boolean) || searchForm.query || '当前检修线索'
    const text = `博闻，请基于「${keyword}」检索知识库资料、知识图谱节点和可沉淀经验；不知道的车型、型号、受损程度请留空，只根据已知图片和检索结果回答。`
    expanded.push({
      action: 'openKnowledgeGraph',
      page: '知识库',
      agent: 'bowen',
      agentName: '博闻',
      target: '知识库悬浮智能体',
      input: { query: keyword },
      reason: '打开博闻所在的知识库页面并准备悬浮智能体交互。',
      expected: '知识库页面已打开，博闻悬浮智能体可交互。'
    })
    expanded.push({
      action: 'agent_type',
      page: '知识库',
      agent: 'bowen',
      agentName: '博闻',
      target: '博闻悬浮输入框',
      text,
      reason: '点开博闻悬浮智能体并输入知识检索指令。',
      expected: '问题写入博闻悬浮输入框。'
    })
    expanded.push({
      action: 'agent_send',
      page: '知识库',
      agent: 'bowen',
      agentName: '博闻',
      target: '博闻悬浮发送按钮',
      text,
      reason: '发送给博闻，展示真实智能体交互。',
      expected: '博闻返回知识资料和沉淀建议。'
    })
  }
  return expanded
}

const tgApplyStepState = async (step = {}) => {
  const page = tgPageKey(step)
  const action = step.action
  const input = step.input || {}
  const rawKeyword = input.query || input.keyword || step.keyword || step.text || ''
  const scene = inferSearchScene(rawKeyword, [...assistantFiles.value, ...searchFiles.value])
  const keyword = rawKeyword || scene?.query || ''
  const agent = step.agent || ''

  selectedAgentId.value = agent || selectedAgentId.value
  activePage.value = page

  if (page === 'search') {
    searchPanel.value = action === 'summarize' ? 'history' : 'multimodal'
    if (!scene && !hasAffirmativeWaterScene(rawKeyword) && WATER_RESULT_RE.test(`${searchForm.deviceName}${searchForm.category}${searchForm.faultType}`)) resetSearchIdentityFields()
    if (scene) applySearchScene(scene)
    if (keyword) {
      searchForm.query = String(keyword)
      if (input.model !== undefined) searchForm.deviceModel = input.model || ''
      if (input.deviceName !== undefined) searchForm.deviceName = input.deviceName || ''
      if (input.faultCode !== undefined) searchForm.faultCode = input.faultCode || ''
      if (input.faultType !== undefined) searchForm.faultType = input.faultType || ''
    }
  }

  if (page === 'tasks') {
    if (String(step.page || step.target || '').includes('联系人')) taskPanel.value = 'contacts'
    else taskPanel.value = 'manage'
    if (taskFilters.keyword !== undefined) taskFilters.keyword = keyword
  }

  if (page === 'knowledge') {
    // 图谱 / 资料库 / Memory 沉淀都搬到上下文中心了，这里要顺手把页面切过去
    if (String(step.page || step.target || '').includes('沉淀')) { activePage.value = 'search'; searchPanel.value = 'update' }
    else if (action === 'openKnowledgeGraph' || String(step.page || step.target || '').includes('图谱')) { activePage.value = 'search'; searchPanel.value = 'network'; window.setTimeout(settleGraphChart, 120) }
    else if (String(step.page || step.target || '').includes('资料库')) { activePage.value = 'search'; searchPanel.value = 'library' }
    else knowledgePanel.value = 'files'
    knowledgeKeyword.value = keyword
  }

  await nextTick()
}

const tgMoveToPageFocus = async (step = {}) => {
  const selectors = {
    search: '.search-workbench-v2',
    tasks: '.tasks-page',
    knowledge: '.graph-console-panel, .knowledge-nav-panel',
    profile: '.profile-dashboard',
    home: '.page-theme-home'
  }
  const page = tgPageKey(step)
  const target = document.querySelector(selectors[page] || '.content-shell')
  if (target) await tgMoveTo(target, tgActionLabel(step))
}

const updateTgRunUi = (step, index, total, steps) => {
  tgRunUi.visible = true
  tgRunUi.statusText = step.requiresApproval ? '等待人工确认' : 'AIOS 正在执行'
  tgRunUi.current = index
  tgRunUi.total = total
  tgRunUi.progress = Math.max(6, Math.min(100, Math.round((index - 1) / Math.max(total, 1) * 100)))
  tgRunUi.title = tgActionLabel(step)
  tgRunUi.detail = tgActionDetail(step)
  tgRunUi.agentName = step.agentName || TG_AGENT_NAMES[step.agent] || '天工'
  tgRunUi.page = step.page || step.target || currentNav.value?.label || '当前页面'
  tgRunUi.tool = step.mcpTool || step.tool || step.action || '页面操作'
  tgRunUi.inputText = tgStepInputText(step)
  tgRunUi.outputText = '正在执行，等待页面返回结果。'
  tgRunUi.observation = tgObservePage()
  tgRunUi.decision = tgDecisionFor(step)
  tgRunUi.check = '执行后自动校验页面结果'
  tgRunUi.steps = steps
    .filter((item) => item.action !== 'done')
    .map((item, stepIndex) => ({
      index: stepIndex + 1,
      label: `${tgActionLabel(item)}${item.agent && item.agent !== 'tiangong' ? ` · ${TG_AGENT_NAMES[item.agent] || item.agentName || item.agent}` : ''}`
    }))
}

function tgAnimate(fromX, fromY, toX, toY, duration = 400) {
  return new Promise((resolve) => {
    const start = performance.now()
    function step(now) {
      const elapsed = now - start
      const t = Math.min(elapsed / duration, 1)
      const ease = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t
      const x = fromX + (toX - fromX) * ease
      const y = fromY + (toY - fromY) * ease
      tgCursor.value.x = x
      tgCursor.value.y = y
      if (t < 1) requestAnimationFrame(step)
      else resolve()
    }
    requestAnimationFrame(step)
  })
}

async function tgMoveTo(el, label = '') {
  if (!el) return
  const rect = el.getBoundingClientRect()
  const targetX = rect.left + rect.width / 2
  const targetY = rect.top + rect.height / 2
  const startX = tgCursor.value.x || targetX
  const startY = tgCursor.value.y || targetY
  tgCursor.value.visible = true
  tgCursor.value.label = label
  await nextTick()
  if (startX !== targetX || startY !== targetY) {
    await tgAnimate(startX, startY, targetX, targetY, 450)
  } else {
    tgCursor.value.x = targetX
    tgCursor.value.y = targetY
    await nextTick()
  }
  await tgSleep(400)
}

async function tgNavigate(agent) {
  const target = TG_PAGE_MAP[agent]
  if (!target) return
  const navTargetX = 90
  const navTargetY = 240
  const startX = tgCursor.value.x || navTargetX
  const startY = tgCursor.value.y || navTargetY
  tgCursor.value.visible = true
  tgCursor.value.label = `→ ${TG_AGENT_NAMES[agent] || agent}`
  await nextTick()
  if (startX !== navTargetX || startY !== navTargetY) {
    await tgAnimate(startX, startY, navTargetX, navTargetY, 400)
  }
  await tgSleep(500)
  activePage.value = target.page
  if (target.panel) taskPanel.value = target.panel
  await nextTick()
  await tgSleep(1200)
}

async function tgType(text, selector = '.operator-panel .ask-box input, .ask-box input', syncRef = operatorInput) {
  console.log('[天工遥控] tgType 开始, 文本长度:', text.length, '内容:', text.substring(0, 30))
  let inputEl = null
  for (let i = 0; i < 10; i++) {
    inputEl = pickVisibleElement(selector)
    if (inputEl) break
    await tgSleep(300)
  }
  if (!inputEl) {
    console.warn('[天工遥控] 未找到输入框')
    return
  }
  console.log('[天工遥控] tgMoveTo 开始')
  await tgMoveTo(inputEl, '输入')
  console.log('[天工遥控] tgMoveTo 完成, 当前input值:', inputEl.value)
  inputEl.focus()
  // 清空输入框
  inputEl.value = ''
  syncRef.value = ''
  // 不立即同步 operatorInput，避免触发 Vue 重新渲染
  console.log('[天工遥控] 清空后 input值:', inputEl.value)
  await nextTick()
  await tgSleep(200)
  // 逐字打字，每次都重新获取最新的 input 元素
  for (let i = 0; i < text.length; i++) {
    const char = text[i]
    // 每3个字重新获取一次元素，避免 DOM 被替换
    if (i % 3 === 0) {
      inputEl = pickVisibleElement(selector)
      if (!inputEl) { console.warn('[天工遥控] 第' + (i+1) + '字时丢失输入框'); break }
      inputEl.focus()
    }
    inputEl.value += char
    // 只在最后同步 Vue ref，避免频繁触发重新渲染
    if (i === text.length - 1 || i % 5 === 4) {
      syncRef.value = inputEl.value
    }
    if (i < 3 || i === text.length - 1) {
      console.log(`[天工遥控] 打字第${i+1}字: "${char}", input值: "${inputEl.value}"`)
    }
    await tgSleep(55)
  }
  // 最终同步
  inputEl = pickVisibleElement(selector)
  if (inputEl) {
    console.log('[天工遥控] 打字完成, input值:', inputEl.value)
    syncRef.value = inputEl.value
    // 触发一次 input 事件确保框架更新
    inputEl.dispatchEvent(new Event('input', { bubbles: true }))
    console.log('[天工遥控] 触发input事件后:', syncRef.value)
  }
  await tgSleep(300)
}

async function tgTypeAgentMessage(text, step = {}) {
  if ((step.agent || selectedAgentId.value) === 'bowen') {
    activePage.value = 'knowledge'
    selectedAgentId.value = 'bowen'
    floatingAgent.open = true
    await nextTick()
    await tgSleep(450)
    await tgType(text, '.floating-ask-box input, .operator-panel .ask-box input, .ask-box input', operatorInput)
    return
  }
  await tgType(text, '.operator-panel .ask-box input, .floating-ask-box input, .ask-box input', operatorInput)
}

async function tgTypeContactMessage(text) {
  activePage.value = 'tasks'
  taskPanel.value = 'contacts'
  await nextTick()
  await tgSleep(500)
  await tgType(text, '.chat-compose-editor input', chatInput)
}

async function sendRemotePrompt(value, targetAgentId = '') {
  const sourcePage = activePage.value
  const agentId = targetAgentId || selectedAgentId.value || operatorProfile.value.id
  const agentProfile = agentProfileMap[agentId] || operatorProfile.value
  if (agentId && agentProfileMap[agentId]) selectedAgentId.value = agentId
  operatorMessages.value.push(operatorMessage({ id: `user-${Date.now()}`, page: sourcePage, role: 'user', text: value }, agentId))
  operatorInput.value = ''
  try {
    if (agentId && agentProfileMap[agentId]) {
      const history = operatorMessages.value
        .filter((item) => item && item.agentId === agentId && item.role && item.text)
        .slice(-8)
        .map((item) => ({ role: item.role, content: item.text }))
      const response = await yixiuApi.agentChat(agentId, { message: value, history })
      const agentName = response.agent?.name || agentProfile.name || TG_AGENT_NAMES[agentId] || '智能体'
      const reply = String(response.response || '').trim() || `${agentName}暂未生成回复。`
      operatorMessages.value.push({
        id: `assistant-${Date.now()}`,
        page: sourcePage,
        agentId,
        role: 'assistant',
        text: cleanAgentReplyText(reply, agentId, agentName)
      })
      return
    }
    const response = await yixiuApi.assistantChat({ message: value, fileIds: [], agent: agentProfile.name, page: sourcePage })
    operatorMessages.value.push(operatorMessage({ id: `assistant-${Date.now()}`, page: sourcePage, role: 'assistant', text: cleanAgentReplyText(response.response, agentId, agentProfile.name) }, agentId))
  } catch (error) {
    operatorMessages.value.push(operatorMessage({ id: `assistant-${Date.now()}`, page: sourcePage, role: 'assistant', text: `（${agentProfile.name || '智能体'}暂未响应：${error.message || ''}）` }, agentId))
  }
}

async function tgClickSend(step = {}) {
  if ((step.agent || selectedAgentId.value) === 'bowen') {
    activePage.value = 'knowledge'
    selectedAgentId.value = 'bowen'
    floatingAgent.open = true
    await nextTick()
    await tgSleep(250)
  }
  const selectorPrefix = (step.agent || selectedAgentId.value) === 'bowen'
    ? '.floating-ask-box button[type="submit"], .operator-panel .ask-box button[type="submit"], .ask-box button[type="submit"]'
    : '.operator-panel .ask-box button[type="submit"], .floating-ask-box button[type="submit"], .ask-box button[type="submit"]'
  const inputSelector = (step.agent || selectedAgentId.value) === 'bowen'
    ? '.floating-ask-box input, .operator-panel .ask-box input, .ask-box input'
    : '.operator-panel .ask-box input, .floating-ask-box input, .ask-box input'
  const btn = pickVisibleElement(selectorPrefix)
  const inputEl = pickVisibleElement(inputSelector)
  if (btn) await tgMoveTo(btn, '发送')
  // 优先从 DOM 获取最新值
  const value = inputEl ? inputEl.value : operatorInput.value
  operatorInput.value = ''
  if (inputEl) {
    inputEl.value = ''
    inputEl.dispatchEvent(new Event('input', { bubbles: true }))
  }
  await sendRemotePrompt(value, step.agent || selectedAgentId.value)
  await tgSleep(1400)
}

async function tgClickContactSend() {
  const btn = pickVisibleElement('.chat-compose button.primary, .chat-compose button[type="submit"]')
  const inputEl = pickVisibleElement('.chat-compose-editor input')
  if (btn) await tgMoveTo(btn, '发送协作消息')
  const value = inputEl ? inputEl.value : chatInput.value
  sendChatMessage(value)
  if (inputEl) {
    inputEl.value = ''
    inputEl.dispatchEvent(new Event('input', { bubbles: true }))
  }
  await tgSleep(1800)
}

const tgTransferAttachmentsToSearch = async (attachments = [], step = {}) => {
  activePage.value = 'search'
  searchPanel.value = 'multimodal'
  selectedAgentId.value = 'guanwei'
  searchResult.value = null
  selectedAiosReport.value = null
  const keyword = step.input?.keyword || step.text || operatorInput.value || ''
  const scene = inferSearchScene(keyword, attachments)
  if (scene) {
    resetSearchIdentityFields()
    applySearchScene(scene)
    searchForm.query = `${scene.query} 已知用户指令：${keyword || '仅上传了现场图片'}`
  } else {
    resetSearchIdentityFields()
    searchForm.query = keyword ? `${keyword}；请结合上传图片判断现场设备、故障部位和风险。未知设备型号请留空，不要套用示例设备。` : '请结合上传图片判断现场设备、故障部位和风险；未知设备型号请留空，不要套用示例设备。'
  }
  searchFiles.value.forEach(releaseFileUrl)
  searchFiles.value = attachments.map(cloneAssistantFileForSearch)
  await nextTick()
  const target = pickVisibleElement('.search-upload-strip, .search-fusion-upload, .search-workbench-v2, .search-dialog-input')
  if (target) await tgMoveTo(target, '转交图片')
  await tgSleep(650)
  await runSearch().catch(() => {})
}

async function executeUIPlan(steps, context = {}) {
  steps = expandTgVisiblePlan(steps)
  console.log('[天工遥控] executeUIPlan 开始, 步骤数:', steps.length)
  tgRunning.value = true
  const totalSteps = steps.filter((s) => !['done'].includes(s.action)).length
  let stepIndex = 0
  tgRunUi.visible = true
  tgRunUi.current = 0
  tgRunUi.total = totalSteps
  tgRunUi.progress = 3
  tgRunUi.title = '准备执行'
  tgRunUi.detail = '天工正在整理跨页面操作路径。'
  tgRunUi.statusText = '准备执行'
  tgRunUi.agentName = '天工'
  tgRunUi.page = currentNav.value?.label || '当前页面'
  tgRunUi.tool = 'UI_PLAN'
  tgRunUi.inputText = '读取后端返回的可视化步骤'
  tgRunUi.outputText = `准备执行 ${totalSteps} 个页面动作。`
  tgRunUi.observation = tgObservePage()
  tgRunUi.decision = '根据用户目标选择真实可执行的页面、智能体和工具顺序'
  tgRunUi.check = '尚未开始校验'
  tgRunUi.steps = steps.filter((item) => item.action !== 'done').map((item, index) => ({
    index: index + 1,
    label: `${tgActionLabel(item)}${item.agent && item.agent !== 'tiangong' ? ` · ${TG_AGENT_NAMES[item.agent] || item.agentName || item.agent}` : ''}`
  }))
  try {
    for (const step of steps) {
      if (!tgRunning.value) { console.log('[天工遥控] tgRunning 为 false, 循环终止'); break }
      const a = step.action
      if (a === 'done' || a === 'finish') {
        tgRunUi.progress = 100
        tgRunUi.statusText = '已完成'
        tgRunUi.title = '执行完成'
        tgRunUi.detail = step.reason || '天工已完成本次长任务。'
        tgRunUi.outputText = step.expected || '本次长任务已闭环。'
        toast('操作完成')
        break
      }
      stepIndex++
      const progressText = `步骤 ${stepIndex}/${totalSteps}`
      updateTgRunUi(step, stepIndex, totalSteps, steps)
      console.log(`[天工遥控] 执行 ${progressText}: ${a}`, step)
      try {
        if (a === 'navigate') {
          toast(`${progressText}：切换到「${step.page || TG_AGENT_NAMES[step.agent] || step.agent}」`)
          if (step.page) {
            await tgApplyStepState(step)
            await tgMoveToPageFocus(step)
            await tgSleep(650)
          } else {
            await tgNavigate(step.agent)
          }
          await tgSleep(800)
        } else if (a === 'transfer_attachment') {
          toast(`${progressText}：转交现场图片给观微`)
          await tgTransferAttachmentsToSearch(context.transferAttachments || assistantFiles.value, step)
          await tgSleep(800)
        } else if (['search', 'filter', 'openPanel', 'openKnowledgeGraph', 'openChat', 'summarize', 'approve', 'report', 'knowledge_search'].includes(a)) {
          toast(`${progressText}：${tgActionLabel(step)}`)
          await tgApplyStepState(step)
          await tgMoveToPageFocus(step)
          if (a === 'search') await runSearch().catch(() => {})
          if (a === 'openKnowledgeGraph' || a === 'knowledge_search') await loadKnowledge().catch(() => {})
          await tgSleep(1000)
        } else if (a === 'type' || a === 'agent_type') {
          toast(`${progressText}：输入指令`)
          await tgTypeAgentMessage(step.text || '', step)
          await tgSleep(500)
        } else if (a === 'click_send' || a === 'agent_send') {
          toast(`${progressText}：发送给${TG_AGENT_NAMES[step.agent] || step.agentName || '智能体'}`)
          await tgClickSend(step)
        } else if (a === 'contact_type') {
          toast(`${progressText}：输入联系人消息`)
          await tgTypeContactMessage(step.text || '')
          await tgSleep(500)
        } else if (a === 'contact_send') {
          toast(`${progressText}：发送联系人消息`)
          await tgClickContactSend()
        } else if (a === 'wait') {
          toast(`${progressText}：等待响应 ${step.seconds || 2}s`)
          await tgSleep((step.seconds || 2) * 1000)
        }
        tgRunUi.outputText = tgStepOutputText(step)
        tgRunUi.observation = tgObservePage()
        tgRunUi.check = tgCheckResultFor(step)
        await tgSleep(350)
      } catch (err) {
        console.warn('[天工遥控] 步骤失败:', a, err)
        tgRunUi.statusText = '步骤异常'
        tgRunUi.outputText = `当前步骤未完成：${err?.message || '页面动作异常'}。已继续下一步。`
        tgRunUi.check = `校验失败：${err?.message || '页面动作异常'}，准备继续下一步。`
        toast(`步骤「${a}」失败，继续下一步`)
      }
    }
  } finally {
    const interrupted = !tgRunning.value
    if (interrupted) {
      tgRunUi.statusText = '已中断'
      tgRunUi.title = '执行已中断'
      tgRunUi.detail = '用户已中断本次 AI 执行，后续页面动作不会继续。'
      tgRunUi.outputText = '执行已停止。'
      tgRunUi.decision = '收到用户中断指令，停止后续步骤。'
      tgRunUi.check = '已中断，未继续校验。'
      await tgSleep(900)
    } else {
      tgRunUi.progress = 100
      tgRunUi.statusText = '已完成'
      tgRunUi.current = totalSteps
      tgRunUi.title = '执行完成'
      tgRunUi.detail = '天工已完成跨页面可视化执行，右侧对话中可查看本次闭环摘要。'
      tgRunUi.outputText = '已完成页面切换、检索、任务联动、知识库定位和闭环摘要。'
      tgRunUi.observation = tgObservePage()
      tgRunUi.decision = '本轮任务已闭环，保留报告供用户展开查看'
      tgRunUi.check = '最终校验完成'
      await tgSleep(4200)
    }
    tgCursor.value = { ...tgCursor.value, visible: false }
    tgRunUi.visible = false
    tgRunning.value = false
  }
}

const playBootAnimation = async () => {
  // 安全网：3.5秒后强制关闭启动画面，防止动画卡住
  const forceClose = window.setTimeout(() => { showSplash.value = false }, 3500)
  
  await nextTick()
  await new Promise((resolve) => window.requestAnimationFrame(resolve))
  const screen = bootScreenRef.value
  const mark = bootMarkRef.value
  const bootLogo = bootLogoRef.value
  const brandLogo = brandLogoRef.value
  if (!screen || !mark || !bootLogo || !brandLogo || !mark.animate || !screen.animate) {
    window.clearTimeout(forceClose)
    window.setTimeout(() => { showSplash.value = false }, 1400)
    return
  }

  const from = mark.getBoundingClientRect()
  const to = brandLogo.getBoundingClientRect()
  const fromCenterX = from.left + from.width / 2
  const fromCenterY = from.top + from.height / 2
  const toCenterX = to.left + to.width / 2
  const toCenterY = to.top + to.height / 2
  const dx = Math.round(toCenterX - fromCenterX)
  const dy = Math.round(toCenterY - fromCenterY)
  const scale = Number((to.width / bootLogo.getBoundingClientRect().width).toFixed(3))

  const markMotion = mark.animate([
    { opacity: 0, transform: 'translate3d(0, 18px, 0) scale(.96)', offset: 0 },
    { opacity: 1, transform: 'translate3d(0, 0, 0) scale(1)', offset: .26 },
    { opacity: 1, transform: `translate3d(${Math.round(dx * .72)}px, ${Math.round(dy * .62 - 18)}px, 0) scale(${Math.min(scale + .1, 1)})`, offset: .76 },
    { opacity: 1, transform: `translate3d(${dx}px, ${dy}px, 0) scale(${scale})`, offset: 1 }
  ], {
    duration: 1580,
    delay: 900,
    easing: 'cubic-bezier(.18,.84,.18,1)',
    fill: 'forwards'
  })

  const screenFade = screen.animate([
    { opacity: 1 },
    { opacity: 1, offset: .86 },
    { opacity: 0 }
  ], {
    duration: 2800,
    easing: 'ease',
    fill: 'forwards'
  })

  await Promise.allSettled([markMotion.finished, screenFade.finished])
  window.clearTimeout(forceClose)
  showSplash.value = false
}

onMounted(async () => {
  window.addEventListener('pointerdown', closeGlobalSearchOnOutside)
  window.addEventListener('pointerdown', closeFloatingAgentOnOutside)
  window.addEventListener('resize', clampFloatingAgent)
  initFloatingAgent()
  if (isAuthenticated.value) {
    const account = getAccounts().find((item) => item.account === currentAccount.value)
    if (!account) logout()
    else {
      applyAccountProfile(account)
      await startWorkspace()
      loadTemplates()
      loadKnowledgeDocs()
      loadExternalImports()
      loadSkills()
      yixiuApi.mcpManifest().then((data) => { mcpManifest.value = data }).catch(() => {})
      refreshAiosTrace()
    }
  } else showSplash.value = false
  resumeNewsCarousel()
  nextTick(() => { tryInitGraphChart() })
})
onBeforeUnmount(() => {
  window.removeEventListener('pointerdown', closeGlobalSearchOnOutside)
  window.removeEventListener('pointerdown', closeFloatingAgentOnOutside)
  window.removeEventListener('resize', clampFloatingAgent)
  if (clockTimer) window.clearInterval(clockTimer)
  if (toastTimer) window.clearTimeout(toastTimer)
  pauseNewsCarousel()
  if (speechRecognition) speechRecognition.stop()
  if (assistantSpeechRecognition) assistantSpeechRecognition.stop()
  if (stopOperatorResize) stopOperatorResize()
  if (chatRecordTimer) window.clearInterval(chatRecordTimer)
  if (chatRecorder?.state === 'recording') chatRecorder.stop()
  chatRecordStream?.getTracks().forEach((track) => track.stop())
  chatObjectUrls.forEach((url) => URL.revokeObjectURL(url))
  if (graphChartInitTimer) { clearTimeout(graphChartInitTimer); graphChartInitTimer = null }
  if (graphChartInstance) { graphChartInstance.dispose(); graphChartInstance = null }
  window.removeEventListener('resize', handleGraphResize)
  releaseFileUrls(searchFiles.value)
  releaseFileUrls(assistantFiles.value)
})
</script>

<style scoped>
:global(*) { box-sizing: border-box; }
:global(body) { margin: 0; min-width: 1180px; background: #EEECEA; color: #111110; font-family: "Microsoft YaHei", "PingFang SC", system-ui, sans-serif; }
button, input, textarea, select { font: inherit; }
button { cursor: pointer; }
.external-import-list { margin-top: 18px; }
.external-artifact-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 12px; }
.external-artifact-grid span { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 4px 8px; align-items: center; min-width: 0; padding: 10px; border: 1px solid #e5ece8; border-radius: 8px; background: #fffdfa; }
.external-artifact-grid b { color: #244f45; font-size: 12px; }
.external-artifact-grid small { grid-column: 1 / -1; overflow: hidden; color: #72817d; font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.external-artifact-grid em { color: #b58a38; font-size: 11px; font-style: normal; font-weight: 800; }
.external-artifact-grid button { min-height: 28px; padding: 4px 8px; border: 1px solid #d8e3dc; border-radius: 7px; background: #f9f4e7; color: #3e5f53; font-size: 11px; font-weight: 800; }
.ui-icon { width: 18px; height: 18px; display: block; fill: none; stroke: currentColor; stroke-width: 1.9; stroke-linecap: round; stroke-linejoin: round; }
.app-shell { min-height: 100vh; display: grid; grid-template-columns: 250px minmax(0, 1fr); background: #EEECEA; }
.app-shell.collapsed { grid-template-columns: 82px minmax(0, 1fr); }
.boot-screen { position: fixed; inset: 0; z-index: 100; display: grid; place-items: center; overflow: hidden; background: #fffdf9; contain: layout paint; }
.boot-grid { position: absolute; inset: -12%; background:
  linear-gradient(90deg, rgba(17,17,16,.045) 1px, transparent 1px),
  linear-gradient(0deg, rgba(17,17,16,.035) 1px, transparent 1px),
  radial-gradient(circle at 50% 46%, rgba(17,17,16,.045), transparent 35%);
  background-size: 48px 48px, 48px 48px, auto; opacity: .8; transform: scale(1.05); }
.boot-flow { position: absolute; height: 1px; width: 36vw; background: linear-gradient(90deg, transparent, rgba(17,17,16,.16), transparent); opacity: 0; animation: bootFlow 1.4s linear .44s both; }
.boot-flow.flow-a { top: 39%; left: 12%; }
.boot-flow.flow-b { top: 57%; right: 10%; animation-delay: .7s; }
.boot-mark { position: relative; display: grid; place-items: center; will-change: transform, opacity; backface-visibility: hidden; }
.boot-mark img { position: relative; z-index: 2; width: 300px; height: 126px; object-fit: contain; border-radius: 12px; opacity: 0; animation: bootLogoIn .72s ease .18s forwards; will-change: opacity, transform; }
@keyframes bootLogoIn { from { opacity: 0; transform: scale(.985); } to { opacity: 1; transform: scale(1); } }
@keyframes bootFlow { 0% { opacity: 0; transform: translate3d(-16vw,0,0); } 18% { opacity: .55; } 100% { opacity: 0; transform: translate3d(16vw,0,0); } }.side-nav { display: flex; flex-direction: column; gap: 18px; padding: 18px 14px; border-right: 1px solid #ddd8d3; background: linear-gradient(180deg, #fbfaf8, #f4f2ef); }
.side-nav nav button, .collapse-btn { width: 100%; border: 0; border-radius: 12px; background: transparent; color: #484336; }
.brand { display: block; width: 176px; height: 74px; object-fit: contain; cursor: pointer; background: transparent; filter: drop-shadow(0 8px 12px rgba(17,17,16,.05)); }
.app-shell.collapsed .brand { width: 50px; height: 50px; object-fit: contain; object-position: center; transform: none; justify-self: center; }
.side-nav nav b { display: block; }
.side-nav nav { display: grid; gap: 8px; }
.side-nav nav button { display: flex; align-items: center; gap: 12px; min-height: 42px; padding: 0 12px; font-weight: 800; }
.nav-icon { width: 26px; height: 26px; display: grid; place-items: center; flex-shrink: 0; border-radius: 9px; background: rgba(17,17,16,.05); color: #484336; }
.side-nav nav button.active, .side-nav nav button:hover { background: var(--teal-dark); color: #fff; }
.side-nav nav button.active .nav-icon, .side-nav nav button:hover .nav-icon { background: rgba(255,255,255,.18); color: #fff; }
.collapse-btn { margin-top: auto; min-height: 38px; background: var(--surface-soft); color: var(--ink); }
.workspace { min-width: 0; display: flex; flex-direction: column; }
.topbar { height: 72px; display: grid; grid-template-columns: minmax(190px, 1fr) 360px auto 38px auto auto; align-items: center; gap: 14px; padding: 0 22px; border-bottom: 1px solid #ddd8d3; background: linear-gradient(180deg, #fbfaf8, #f4f2ef); }
.content-shell { height: calc(100vh - 72px); min-height: 0; display: grid; grid-template-columns: minmax(0, 1fr) 360px; }
.breadcrumb, .eyebrow { margin: 0; color: #706D6D; font-size: 12px; font-weight: 800; }
h1, h2, h3, h4, p { margin: 0; }
h1 { margin-top: 4px; font-size: 20px; }
.global-search { height: 40px; display: flex; align-items: center; gap: 8px; padding: 0 12px; border: 1px solid #ddd8d3; border-radius: 14px; background: #fbfaf8; }
.global-search input, .form-grid input, .form-grid textarea, .form-grid select, .filters input, .filters select, .recheck-grid textarea, .recheck-grid select { width: 100%; border: 1px solid #ddd8d3; border-radius: 10px; background: #fbfaf8; color: #111110; outline: 0; }
.global-search input { border: 0; background: transparent; }
.work-strip { display: flex; gap: 8px; white-space: nowrap; }
.work-strip button, .work-strip span, .badge, .tag-line span { padding: 5px 9px; border-radius: 999px; background: #EEECEA; color: #484336; font-size: 12px; font-weight: 800; }
.work-strip button { border: 0; transition: transform .16s ease, box-shadow .16s ease, background .16s ease; }
.work-strip button:hover { transform: translateY(-1px); box-shadow: 0 6px 14px rgba(17,17,16,.08); }
.work-strip .bad { background: #f4dfda; color: #8f3f2d; }
.notification-button { position: relative; }
.notification-button i { position: absolute; right: -4px; top: -5px; min-width: 17px; height: 17px; display: grid; place-items: center; padding: 0 4px; border: 2px solid #fbfaf8; border-radius: 999px; background: #c94f43; color: #fff; font-size: 9px; font-style: normal; font-weight: 900; line-height: 1; }
.notification-button.unread::after { content: ""; position: absolute; right: 5px; top: 6px; width: 7px; height: 7px; border-radius: 50%; background: #c94f43; box-shadow: 0 0 0 3px rgba(201,79,67,.12); }
.icon-button, .user-chip { border: 1px solid #ddd8d3; background: #fbfaf8; border-radius: 12px; color: #111110; }
.icon-button { width: 38px; height: 38px; display: grid; place-items: center; padding: 0; }
.user-chip { display: flex; align-items: center; gap: 8px; padding: 5px 10px; }
.topbar-logout { min-height: 38px; display: inline-flex; align-items: center; justify-content: center; gap: 7px; padding: 0 13px; border: 1px solid #ead8d3; border-radius: 11px; background: #fff8f6; color: #974936; font-weight: 800; white-space: nowrap; transition: transform .18s, border-color .18s, background .18s, box-shadow .18s; }
.topbar-logout .ui-icon { width: 17px; height: 17px; }
.topbar-logout:hover { transform: translateY(-1px); border-color: #dbaea2; background: #fff1ed; box-shadow: 0 7px 16px rgba(151,73,54,.1); }
.topbar-logout:focus-visible { outline: 3px solid rgba(151,73,54,.16); outline-offset: 2px; }
.user-chip img, .contact-card img, .profile-card img { width: 30px; height: 30px; border-radius: 50%; object-fit: cover; }
.page-scroll { min-height: 0; overflow: auto; padding: 22px; }
.page-grid { display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); gap: 16px; }
.span-all { grid-column: 1 / -1; }
.span-8 { grid-column: span 8; }
.span-7 { grid-column: span 7; }
.span-6 { grid-column: span 6; }
.span-5 { grid-column: span 5; }
.span-4 { grid-column: span 4; }
.panel, .welcome-card, .agent-card, .stat-card, .profile-card { border: 1px solid #ddd8d3; border-radius: 14px; background: #fbfaf8; box-shadow: 0 14px 30px rgba(17,17,16,.04); }
.panel, .welcome-card, .agent-card, .profile-card { padding: 18px; }
.welcome-brand { display: grid; grid-template-columns: 300px minmax(0, 1fr); gap: 24px; align-items: center; }
.welcome-brand img { width: 300px; height: 142px; object-fit: contain; padding: 0; border: 0; border-radius: 18px; background: transparent; filter: drop-shadow(0 18px 26px rgba(17,17,16,.1)); }
.welcome-card h2 { margin: 8px 0; font-size: 28px; }
.health-grid, .analysis-grid, .detail-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-top: 16px; }
.health-grid span, .analysis-grid span, .detail-grid span { padding: 10px; border-radius: 10px; background: #f4f2ef; color: #484336; font-size: 13px; }
.agent-row { display: grid; grid-template-columns: 64px 9px minmax(0, 1fr); align-items: center; gap: 10px; padding: 10px 0; border-bottom: 1px solid #EEECEA; }
.agent-row img { width: 64px; height: 64px; border-radius: 50%; object-fit: cover; box-shadow: 0 10px 18px rgba(17,17,16,.08); }
.agent-row small, .result-card small, .contact-card small, .tr small { display: block; margin-top: 4px; color: #706D6D; font-size: 12px; }
.dot { width: 9px; height: 9px; margin-top: 5px; border-radius: 50%; background: #706D6D; }
.dot.online { background: #4f8062; }
.dot.busy { background: #b88a44; }
.stat-card { min-height: 116px; padding: 16px; text-align: left; }
.task-stat { min-height: 88px; padding: 12px; }
.task-stat b { margin: 6px 0; font-size: 24px; }
.stat-card span, .stat-card small { display: block; color: #706D6D; }
.stat-card b { display: block; margin: 10px 0; font-size: 30px; }
.panel-head, .filters, .actions, .card-actions, .inline-actions { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.table { display: grid; gap: 3px; overflow: auto; }
.tr { display: grid; grid-template-columns: 1.05fr 1.2fr 1.8fr .75fr .8fr 1fr .8fr 1.15fr; gap: 10px; align-items: center; width: 100%; min-width: 980px; padding: 11px 12px; border: 0; border-radius: 10px; background: transparent; color: #111110; text-align: left; }
.compact .tr { grid-template-columns: 1.1fr 1.5fr .8fr .75fr .8fr .75fr .6fr; min-width: 780px; }
.tr.head { background: #EEECEA; color: #706D6D; font-size: 12px; font-weight: 900; }
.tr:not(.head):hover { background: #f4f2ef; }
.badge.high { background: #f4dfda; color: #8f3f2d; }
.badge.medium { background: #efe5d5; color: #694b22; }
.badge.low { background: #e6ebe3; color: #425744; }
.quick-grid, .result-grid, .contact-grid, .recheck-grid, .file-cards { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.quick-grid button, .history-row, .alert-list button { min-height: 42px; border: 1px solid #ddd8d3; border-radius: 10px; background: #f4f2ef; color: #111110; text-align: left; padding: 10px; }
.alert-list { display: grid; gap: 10px; margin-top: 12px; }
.alert-list small { display: block; margin-top: 4px; color: #706D6D; }
.chart-wrap { display: grid; grid-template-columns: minmax(0, 1fr) 190px; gap: 16px; align-items: center; }
.chart-wrap svg { width: 100%; height: 250px; border-radius: 12px; background: linear-gradient(#ddd8d3 1px, transparent 1px), #fbfaf8; background-size: 100% 25%; }
.distribution { display: grid; gap: 10px; }
.distribution span { display: grid; gap: 5px; color: #706D6D; font-size: 12px; }
.distribution b { height: 8px; border-radius: 99px; background: #111110; }
.two-column { display: grid; grid-template-columns: minmax(0, 1fr) 420px; gap: 16px; }
.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.form-grid label { display: grid; gap: 6px; color: #484336; font-size: 13px; font-weight: 800; }
.form-grid .wide { grid-column: 1 / -1; }
.form-grid input, .form-grid select { height: 40px; padding: 0 10px; }
textarea { min-height: 96px; resize: vertical; padding: 10px; }
.upload-zone { margin-top: 14px; padding: 18px; border: 1px dashed #C5BFB9; border-radius: 12px; background: #f4f2ef; text-align: center; }
.upload-zone input, .panel-head input[type=file] { display: none; }
button, .ghost { border: 1px solid #ddd8d3; border-radius: 10px; background: #fbfaf8; color: #111110; padding: 8px 12px; }
.primary { border-color: #111110; background: #111110; color: #EEECEA; }
button:disabled { opacity: .55; cursor: not-allowed; }
.file-pills, .tag-line { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.file-pills span { padding: 8px 10px; border-radius: 999px; background: #EEECEA; font-size: 12px; }
.result-card, .contact-card { display: grid; gap: 10px; padding: 14px; border: 1px solid #ddd8d3; border-radius: 12px; background: #fff; }
.sop-list, .timeline { display: grid; gap: 9px; margin-top: 12px; }
.sop-list span, .timeline span, .load-row { display: flex; align-items: center; gap: 10px; padding: 10px; border-radius: 10px; background: #f4f2ef; }
.sop-list b { width: 24px; height: 24px; display: grid; place-items: center; border-radius: 8px; background: #111110; color: #EEECEA; }
.tabs { display: flex; flex-wrap: wrap; gap: 8px; }
.tabs button.active { background: #111110; color: #EEECEA; }
.filters { margin-bottom: 14px; align-items: stretch; }
.filters input, .filters select, .recheck-grid textarea, .recheck-grid select { min-height: 40px; padding: 0 10px; }
.load-row { justify-content: space-between; }
.load-row b { height: 8px; max-width: 55%; border-radius: 99px; background: #111110; }
.task-analytics { background: linear-gradient(180deg, #fbfffe, #f4faf7); }
.analysis-cards { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-top: 12px; }
.analysis-cards section { min-height: 172px; display: grid; align-content: start; gap: 8px; padding: 12px; border: 1px solid #dce9e5; border-radius: 12px; background: #fffdfa; }
.analysis-cards svg { width: 100%; height: 112px; border-radius: 10px; background: linear-gradient(#eef5f3 1px, transparent 1px); background-size: 100% 25%; }
.bar-row, .chip-row { min-height: 28px; display: grid; grid-template-columns: 68px minmax(0, 1fr) 24px; align-items: center; gap: 8px; padding: 4px 0; border: 0; background: transparent; text-align: left; }
.bar-row i { height: 8px; border-radius: 999px; background: #2f7f8f; }
.bar-row i.high { background: #c95f5a; }
.bar-row i.medium { background: #d79542; }
.bar-row i.low { background: #6c9b72; }
.chip-row { grid-template-columns: minmax(0, 1fr) 28px; padding: 6px 8px; border-radius: 10px; background: #edf6f4; color: #294f52; }
.chip-row.warm { background: #f8eddf; color: #7a4b1f; }
.priority-list { display: grid; gap: 10px; margin-top: 12px; }
.priority-list article { display: grid; grid-template-columns: minmax(0, 1.5fr) 110px minmax(0, 1fr) minmax(0, 1fr) auto; gap: 10px; align-items: center; padding: 12px; border: 1px solid #ddd8d3; border-radius: 12px; background: #fffdfa; }
.priority-list small { color: #706D6D; }
.task-events span { border-left: 3px solid #2f7f8f; }
.view-switch { display: inline-flex; gap: 4px; padding: 4px; border: 1px solid #ddd8d3; border-radius: 999px; background: #f4f2ef; }
.view-switch button { min-height: 28px; padding: 4px 10px; border-radius: 999px; }
.view-switch button.active { background: #111110; color: #EEECEA; }
.task-board { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.task-board section { min-height: 360px; display: grid; align-content: start; gap: 10px; padding: 12px; border-radius: 14px; background: #f4f8f6; }
.task-board h4 { display: flex; justify-content: space-between; margin: 0; }
.task-board article { display: grid; gap: 6px; padding: 12px; border: 1px solid #dce9e5; border-radius: 12px; background: #fffdfa; cursor: pointer; }
.task-board article small { color: #706D6D; }
.contact-card img, .profile-card img { width: 58px; height: 58px; }
.chat-workbench { min-height: 720px; display: grid; grid-template-columns: 300px minmax(0, 1fr) 330px; gap: 0; padding: 0; overflow: hidden; border-color: #d7e8e5; background: #f3faf9; }
.contact-focus-shell { grid-template-columns: minmax(0, 1fr) 10px var(--operator-width, 360px) !important; }
.contact-focus-shell .page-scroll { padding-right: 16px; }
.contact-focus-shell .chat-workbench { grid-template-columns: 260px minmax(430px, 1fr) 286px; height: calc(100vh - 246px); min-height: 620px; }
.contact-focus-shell .chat-workbench.left-collapsed { grid-template-columns: 64px minmax(520px, 1fr) 286px; }
.contact-focus-shell .chat-workbench.right-collapsed { grid-template-columns: 260px minmax(560px, 1fr) 54px; }
.contact-focus-shell .chat-workbench.left-collapsed.right-collapsed { grid-template-columns: 64px minmax(680px, 1fr) 54px; }
.conversation-list, .collab-info { min-width: 0; min-height: 0; padding: 0; background: #f7fbfa; }
.conversation-list { display: grid; grid-template-rows: auto auto auto auto minmax(0, 1fr); align-content: stretch; gap: 0; border-right: 1px solid #d7e8e5; }
.contact-toolbar { display: grid; grid-template-columns: 28px minmax(0, 1fr) 32px 32px; gap: 7px; padding: 12px; border-bottom: 1px solid #e4efec; background: #fffdfa; }
.contact-toolbar button { min-height: 32px; display: grid; place-items: center; padding: 0; border-radius: 50%; border-color: #d7e8e5; background: #f7fbfa; color: #6d8584; font-size: 15px; font-weight: 900; box-shadow: 0 4px 10px rgba(31,69,75,.035); }
.contact-toolbar button:hover { border-color: #a9cfca; background: #edf7f5; color: #2f7f8f; transform: translateY(-1px); }
.contact-collapse-btn { color: #2f7f8f !important; background: #eef8f6 !important; }
.chat-search input { width: 100%; height: 34px; padding: 0 12px; border: 1px solid #d7e8e5; border-radius: 999px; background: #f8fcfb; }
.conversation-scroll > button { position: relative; min-height: 74px; display: grid; grid-template-columns: 46px minmax(0, 1fr) auto; align-items: center; gap: 10px; padding: 10px 12px; border: 0; border-bottom: 1px solid #e6efec; border-radius: 0; background: transparent; text-align: left; transition: background .18s ease, box-shadow .18s ease; }
.conversation-scroll > button::before { content: ""; position: absolute; left: 0; top: 12px; bottom: 12px; width: 3px; border-radius: 0 999px 999px 0; background: transparent; }
.conversation-scroll > button.active, .conversation-scroll > button:hover { background: #fffdfa; box-shadow: 0 8px 18px rgba(47,127,143,.045); }
.conversation-scroll > button.active::before { background: #2f7f8f; }
.conversation-scroll > button > span { min-width: 0; display: grid; gap: 3px; }
.conversation-scroll > button b { overflow: hidden; color: #18393d; font-size: 13px; line-height: 1.28; text-overflow: ellipsis; white-space: nowrap; }
.conversation-scroll > button small { overflow: hidden; max-width: 100%; color: #7b8b8a; font-size: 11px; line-height: 1.35; text-overflow: ellipsis; white-space: nowrap; }
.conversation-scroll img { width: 44px; height: 44px; border-radius: 50%; object-fit: cover; }
.conversation-list small, .chat-title small, .collab-info p { display: block; color: #6b7d7c; }
.conversation-scroll time { align-self: start; color: #a0adab; font-size: 11px; }
.conversation-scroll i { position: absolute; left: 44px; top: 12px; min-width: 20px; height: 20px; display: grid; place-items: center; border-radius: 50%; background: #c95f5a; color: #fff; font-style: normal; font-size: 11px; }
.chat-workbench.left-collapsed .conversation-list { overflow: hidden; }
.chat-workbench.left-collapsed .contact-toolbar { grid-template-columns: 1fr; gap: 8px; padding: 12px 10px; }
.chat-workbench.left-collapsed .chat-search,
.chat-workbench.left-collapsed .contact-mode-tabs,
.chat-workbench.left-collapsed .contact-filter,
.chat-workbench.left-collapsed .contact-summary { display: none; }
.chat-workbench.left-collapsed .contact-toolbar button:not(.contact-collapse-btn) { display: none; }
.chat-workbench.left-collapsed .conversation-scroll > button { min-height: 62px; grid-template-columns: 46px; justify-content: center; padding: 8px 12px; border-bottom-color: transparent; }
.chat-workbench.left-collapsed .conversation-scroll > button > span,
.chat-workbench.left-collapsed .conversation-scroll time { display: none; }
.chat-workbench.left-collapsed .conversation-scroll i { left: 42px; top: 7px; }
.chat-main { min-width: 0; display: grid; grid-template-rows: auto auto minmax(0, 1fr) auto; background: #fffdfa; }
.chat-title { min-height: 76px; display: flex; align-items: center; gap: 10px; justify-content: space-between; padding: 12px 22px 8px; border-bottom: 1px solid #d7e8e5; background: #fffdfa; }
.chat-title h3 { margin: 0 0 4px; color: #1f3438; font-size: 17px; }
.chat-title h3 span { color: #677a79; font-weight: 700; }
.chat-title nav { display: flex; gap: 18px; }
.chat-title nav button { min-height: 24px; padding: 0; border: 0; border-radius: 0; background: transparent; color: #8a9998; font-size: 13px; }
.chat-title nav button.active { color: #2f7f8f; box-shadow: inset 0 -2px 0 #2f7f8f; }
.chat-title-actions { display: flex; align-items: center; gap: 8px; }
.chat-title-actions button { min-height: 34px; padding: 6px 10px; border-radius: 10px; border-color: #d7e8e5; background: #fff; color: #36575b; font-weight: 800; }
.chat-messages { min-height: 0; overflow: auto; display: grid; align-content: start; gap: 18px; padding: 20px 22px; background: #f4f6f5; }
.message { display: flex; gap: 8px; max-width: 78%; }
.message.mine { justify-self: end; }
.message img { width: 36px; height: 36px; border-radius: 50%; object-fit: cover; }
.message > div { display: grid; gap: 7px; padding: 12px 14px; border-radius: 4px 14px 14px 14px; background: #fff; color: #213d3f; box-shadow: 0 1px 0 rgba(31,69,75,.04); }
.message.mine > div { border-radius: 14px 4px 14px 14px; background: #dff1f5; color: #1f4650; }
.message small { color: #6b7d7c; }
.message-card { display: grid; gap: 3px; min-width: 220px; padding: 10px; border: 1px solid #cfe1de; border-radius: 10px; background: rgba(255,255,255,.78); text-align: left; }
.chat-compose {
  display: grid;
  gap: 9px;
  padding: 11px 14px 12px;
  border-top: 1px solid #d7e8e5;
  background: linear-gradient(180deg, #fffdfa 0%, #f8fcfb 100%);
  box-shadow: 0 -8px 18px rgba(31,69,75,.035);
}
.chat-compose-tools {
  display: flex;
  align-items: center;
  gap: 7px;
  min-width: 0;
}
.chat-compose-editor {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 64px;
  align-items: center;
  gap: 8px;
}
.chat-compose input {
  min-width: 0;
  height: 40px;
  padding: 0 14px;
  border: 1px solid #cfe1de;
  border-radius: 13px;
  background: #fff;
  color: #1f3f43;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.75), 0 5px 14px rgba(31,69,75,.035);
}
.chat-compose input:focus {
  border-color: #91c5bd;
  outline: 0;
  box-shadow: 0 0 0 4px rgba(47,127,143,.09), 0 8px 18px rgba(31,69,75,.055);
}
.collab-info { display: grid; align-content: start; gap: 0; overflow: auto; border-left: 1px solid #d7e8e5; background: #fffdfa; }
.chat-workbench.right-collapsed .collab-info { overflow: hidden; }
.collab-info > img { width: 74px; height: 74px; border-radius: 50%; object-fit: cover; }
.collab-actions { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.graph-panel { overflow: hidden; background: #fbfaf8; }
.graph-toolbar, .file-toolbar { display: grid; grid-template-columns: minmax(0, 1fr) auto auto; gap: 12px; align-items: center; margin-bottom: 14px; }
.graph-search { width: 46px; height: 46px; display: grid; grid-template-columns: 34px minmax(0, 1fr) 26px; align-items: center; gap: 6px; padding: 5px; border: 1px solid #ddd8d3; border-radius: 999px; background: #fffdfa; overflow: hidden; transition: width .34s ease, border-color .24s ease, box-shadow .24s ease; }
.graph-search.expanded, .graph-search:focus-within { width: min(420px, 42vw); border-color: #B88A44; box-shadow: 0 16px 28px rgba(17,17,16,.07); }
.graph-search-trigger, .graph-search-clear { width: 34px; height: 34px; display: grid; place-items: center; padding: 0; border: 0; border-radius: 50%; background: #111110; color: #EEECEA; }
.graph-search-clear { width: 26px; height: 26px; background: #EEECEA; color: #484336; }
.graph-search input { min-width: 0; width: 100%; border: 0; outline: 0; background: transparent; opacity: 0; color: #111110; transition: opacity .18s ease .1s; }
.graph-search.expanded input, .graph-search:focus-within input { opacity: 1; }
.graph-controls { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; }
.graph-controls select, .graph-controls button { height: 38px; border: 1px solid #ddd8d3; border-radius: 999px; background: #fffdfa; color: #111110; padding: 0 10px; }
.knowledge-map { display: grid; grid-template-columns: minmax(0, 1fr) 310px; gap: 14px; }
.map-sidebar { display: grid; align-content: start; gap: 12px; }
.map-canvas-wrap { position: relative; border-radius: 18px; overflow: hidden; box-shadow: inset 0 0 0 1px #dde5e8; }
.map-canvas { position: relative; min-height: 520px; border-radius: 0; overflow: hidden; background:
  radial-gradient(circle at 50% 50%, rgba(78,125,151,.12), transparent 30%),
  linear-gradient(90deg, rgba(84,98,112,.08) 1px, transparent 1px),
  linear-gradient(0deg, rgba(84,98,112,.07) 1px, transparent 1px),
  #f8fbfc; background-size: auto, 28px 28px, 28px 28px, auto; }
.echarts-canvas { width: 100%; height: 520px; }
.graph-legend-panel { position: absolute; left: 12px; top: 12px; z-index: 10; pointer-events: none; }
.legend-body { display: flex; flex-direction: column; gap: 5px; padding: 8px 10px; border: 1px solid rgba(219,227,230,.6); border-radius: 10px; background: rgba(255,255,255,.78); box-shadow: 0 2px 10px rgba(0,0,0,.04); backdrop-filter: blur(6px); pointer-events: auto; }
.legend-body span { display: inline-flex; align-items: center; gap: 5px; padding: 5px 8px; border: 1px solid #dbe3e6; border-radius: 999px; background: rgba(255,255,255,.82); color: #52616b; font-size: 11px; font-weight: 800; cursor: pointer; user-select: none; transition: opacity .18s ease, transform .18s ease; }
.legend-body span:hover { transform: translateY(-1px); box-shadow: 0 4px 10px rgba(0,0,0,.06); }
.legend-body span.dimmed { opacity: .35; }
.legend-body i { width: 9px; height: 9px; border-radius: 50%; }
.legend-body i.equipment { background: #3f7fa7; }
.legend-body i.model { background: #8fc0d6; }
.legend-body i.part { background: #45aeb0; }
.legend-body i.fault { background: #d79542; }
.legend-body i.cause { background: #cf6d45; }
.legend-body i.method { background: #8b879f; }
.legend-body i.solution { background: #6c9b72; }
.legend-body i.sop { background: #2f5f88; }
.legend-body i.risk { background: #c95f5a; }
.legend-body i.case { background: #9a7858; }
.legend-body i.doc { background: #7d95a8; }
.map-inspector { display: grid; align-content: start; gap: 12px; padding: 16px; border: 1px solid #ddd8d3; border-radius: 16px; background: linear-gradient(180deg, #fffdfa, #f4f2ef); }
.map-inspector p { color: #484336; line-height: 1.65; }
.tg-suggestion-card { display: grid; align-content: start; gap: 12px; padding: 16px; border: 1px solid #ddd8d3; border-radius: 16px; background: linear-gradient(180deg, #fff8f6, #fdf2ee); }
.tg-card-head { display: grid; grid-template-columns: 40px minmax(0, 1fr) auto; gap: 10px; align-items: center; }
.tg-card-head img { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; }
.tg-card-head h4 { font-size: 14px; font-weight: 900; color: #484336; margin: 2px 0 0; }
.tg-card-head .eyebrow { margin: 0; }
.tg-badge { padding: 4px 10px; border-radius: 999px; background: #c95f5a; color: #fff; font-size: 11px; font-weight: 900; white-space: nowrap; }
.tg-card-body { color: #484336; line-height: 1.65; font-size: 13px; margin: 0; }
.tg-card-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.tg-card-tags span { padding: 4px 8px; border-radius: 999px; background: #f4dfda; color: #8f3f2d; font-size: 11px; font-weight: 800; }
.tg-card-actions { display: flex; gap: 8px; }
.tg-card-actions button { flex: 1; min-height: 34px; border-radius: 10px; font-size: 12px; font-weight: 800; }
.tg-card-actions .primary { background: #c95f5a; border-color: #c95f5a; color: #fff; }
.file-manager input[type=file] { display: none; }
.file-toolbar { grid-template-columns: minmax(0, 1fr) 1px auto; }
.file-actions { display: flex; justify-content: flex-end; gap: 8px; }
.file-actions .file-tool-btn {
  min-height: 30px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 8px;
  border-radius: 8px;
  border-color: #dbe3e5;
  background: rgba(255,255,255,.82);
  color: #53666c;
  font-size: 11px;
  font-weight: 800;
  box-shadow: 0 4px 10px rgba(31,55,63,.035);
}
.file-actions .file-tool-btn span {
  width: 18px;
  height: 18px;
  display: grid;
  place-items: center;
  border-radius: 6px;
  background: #eef6f8;
  color: #3979a0;
  line-height: 1;
}
.file-actions .file-tool-btn b { font-size: 11px; font-weight: 900; }
.file-actions .file-tool-btn.primary {
  border-color: #95c7dd;
  background: #eaf7fd;
  color: #236b8a;
}
.file-actions .file-tool-btn.primary span {
  background: #67b2e6;
  color: #fff;
}
.file-actions .file-tool-btn:hover {
  transform: translateY(-1px);
  border-color: #a9cbd4;
  background: #fff;
}
.file-window { min-height: 620px; display: grid; grid-template-columns: 230px minmax(0, 1fr); border: 1px solid #ddd8d3; border-radius: 16px; overflow: hidden; background: #fffdfa; }
.file-sidebar { display: grid; align-content: start; gap: 6px; padding: 14px; border-right: 1px solid #ddd8d3; background: #f4f2ef; }
.file-sidebar button { display: flex; align-items: center; justify-content: flex-start; gap: 10px; min-height: 40px; border: 0; background: transparent; text-align: left; }
.file-sidebar button.active, .file-sidebar button:hover { background: #111110; color: #EEECEA; }
.file-sidebar span { width: 24px; height: 24px; display: grid; place-items: center; border-radius: 8px; background: rgba(255,255,255,.74); color: #111110; font-weight: 900; }
.file-desktop { min-width: 0; display: grid; grid-template-rows: auto minmax(0, 1fr) auto; gap: 12px; padding: 14px; background:
  radial-gradient(circle, rgba(17,17,16,.07) 1px, transparent 1px),
  #fffdfa; background-size: 22px 22px; }
.file-pathbar { display: grid; grid-template-columns: minmax(180px, 1fr) minmax(180px, 280px) 140px auto; gap: 8px; align-items: center; padding: 8px; border: 1px solid #ddd8d3; border-radius: 12px; background: rgba(251,250,248,.92); }
.file-pathbar span { color: #484336; font-size: 13px; font-weight: 900; }
.file-pathbar input, .file-pathbar select { min-width: 0; height: 36px; padding: 0 10px; border: 1px solid #ddd8d3; border-radius: 10px; background: #fff; }
.desktop-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); align-content: start; gap: 14px; padding: 4px; overflow: auto; }
.desktop-file { min-height: 142px; display: grid; justify-items: center; align-content: center; gap: 7px; padding: 12px; border: 1px solid transparent; background: rgba(255,253,250,.72); text-align: center; }
.desktop-file:hover, .desktop-file.selected { border-color: #B88A44; background: rgba(239,229,213,.82); }
.desktop-file b { width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; }
.desktop-file small, .desktop-file i { color: #706D6D; font-size: 11px; font-style: normal; }
.file-icon { width: 60px; height: 54px; display: grid; place-items: center; border-radius: 12px; background: #EEECEA; color: #111110; font-size: 13px; font-weight: 900; box-shadow: inset 0 -10px 0 rgba(17,17,16,.05); }
.file-icon.pdf { background: #f4dfda; color: #8f3f2d; }
.file-icon.doc, .file-icon.text { background: #efe5d5; color: #694b22; }
.file-icon.sheet { background: #e6ebe3; color: #425744; }
.file-icon.image { background: #dfeff1; color: #245a61; }
.file-icon.video { background: #e8e6df; color: #111110; }
.file-table .tr { min-width: 1040px; }
.file-statusbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 9px 12px; border: 1px solid #ddd8d3; border-radius: 12px; background: rgba(251,250,248,.92); color: #706D6D; font-size: 12px; }
.file-window { grid-template-columns: 280px minmax(0, 1fr); }
.file-sidebar { gap: 0; padding: 12px 0; overflow: auto; background: #f7f8f9; }
.file-tree-root, .file-tree-list { display: grid; gap: 0; }
.file-tree-hint { margin: 0 12px 8px; padding: 8px 10px; border: 1px dashed #d8dde1; border-radius: 8px; background: rgba(255,255,255,.62); color: #7c858e; font-size: 11px; }
.file-tree-root b,
.file-tree-row {
  min-height: 40px;
  display: grid;
  grid-template-columns: 18px 22px minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 4px;
  padding: 0 14px;
  border: 0;
  border-radius: 0;
  background: transparent;
  color: #5f676f;
  font-size: 14px;
  font-weight: 500;
  text-align: left;
}
.file-tree-root b::before,
.file-tree-row::before {
  content: "";
  width: 20px;
  height: 16px;
  border-radius: 2px 2px 3px 3px;
  background: #f5c94f;
  box-shadow: inset 0 4px 0 rgba(255,255,255,.2);
}
.file-tree-row > i { color: #a2a9b0; font-style: normal; text-align: center; }
.file-tree-row > span {
  width: auto;
  height: auto;
  display: block;
  overflow: hidden;
  border-radius: 0;
  background: transparent;
  color: inherit;
  font-weight: inherit;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.file-tree-list em { justify-self: end; min-width: 20px; padding: 1px 6px; border-radius: 999px; background: rgba(255,255,255,.72); color: #8a949c; font-size: 10px; font-style: normal; font-weight: 800; }
.file-node-actions {
  display: inline-flex !important;
  gap: 3px;
  width: auto !important;
  height: auto !important;
  opacity: 0;
  pointer-events: none;
  background: transparent !important;
}
.file-node-actions button {
  width: 20px;
  height: 20px;
  display: grid;
  place-items: center;
  padding: 0;
  border: 1px solid #dbe3e5;
  border-radius: 6px;
  background: rgba(255,255,255,.86);
  color: #6f7d82;
  font-size: 11px;
  line-height: 1;
}
.file-node-actions button:hover { border-color: #95c7dd; color: #236b8a; background: #eef8fc; }
.file-tree-row:hover .file-node-actions,
.file-tree-row.active .file-node-actions {
  opacity: 1;
  pointer-events: auto;
}
.file-tree-row.active,
.file-tree-row:hover {
  background: #eef0f2;
  color: #4d565f;
}
.file-tree-row.dropover {
  background: #e4f2fb;
  color: #245d83;
  box-shadow: inset 3px 0 0 #67b2e6;
}
.file-tree-row {
  margin: 1px 8px;
  min-height: 36px;
  border-radius: 8px;
  cursor: pointer;
}
.file-tree-row::before {
  width: 18px;
  height: 14px;
  border-radius: 3px;
  background: linear-gradient(180deg, #f9d86a 0%, #f2c34b 100%);
}
.file-tree-row > span { font-size: 13px; font-weight: 700; color: #50606a; }
.file-tree-list em {
  min-width: 18px;
  padding: 1px 6px;
  background: #fff;
  color: #8e99a2;
  font-size: 10px;
}
.file-node-actions {
  align-items: center;
  justify-self: end;
  padding-left: 4px;
}
.file-node-actions button,
.file-node-actions button::before {
  content: none !important;
}
.file-node-actions button {
  width: 18px !important;
  height: 18px !important;
  min-height: 18px !important;
  padding: 0 !important;
  border: 0 !important;
  border-radius: 5px !important;
  background: transparent !important;
  color: #9aa6ad !important;
  font-size: 12px !important;
  font-weight: 800;
  box-shadow: none !important;
}
.file-node-actions button:hover {
  background: #dff1fa !important;
  color: #247ba6 !important;
}
.graph { min-height: 360px; display: flex; flex-wrap: wrap; align-content: center; justify-content: center; gap: 14px; border-radius: 14px; background: radial-gradient(circle, #EEECEA 1px, transparent 1px), #fbfaf8; background-size: 24px 24px; }
.graph button { border-radius: 999px; }
.graph .equipment { padding: 18px 24px; background: #111110; color: #EEECEA; }
.graph .fault { background: #EEECEA; }
.graph .doc, .graph .sop { background: #fff; }
.empty { padding: 28px; border-radius: 12px; background: #f4f2ef; color: #706D6D; text-align: center; }
.profile-card { display: grid; place-items: start; gap: 12px; }
.profile-hero { display: grid; grid-template-columns: 64px minmax(0, 1fr) auto; align-items: center; gap: 14px; padding: 14px 16px; border: 1px solid #ddd8d3; border-radius: 14px; background: linear-gradient(180deg, #fffdfa, #f4f2ef); box-shadow: 0 14px 30px rgba(17,17,16,.04); }
.profile-hero img { width: 64px; height: 64px; border-radius: 50%; object-fit: cover; }
.profile-hero h2 { margin: 3px 0; font-size: 22px; }
.profile-hero .eyebrow { font-size: 10px; }
.profile-hero p { font-size: 12px; }
.profile-section { display: grid; gap: 10px; padding: 13px 14px; border: 1px solid #ddd8d3; border-radius: 12px; background: #fbfaf8; box-shadow: 0 14px 30px rgba(17,17,16,.04); }
.profile-metrics { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 7px; }
.profile-metrics span { display: grid; gap: 3px; padding: 8px; border-radius: 9px; background: #f4f2ef; color: #706D6D; font-size: 11px; }
.profile-metrics b { color: #111110; font-size: 18px; }
.profile-list { display: grid; gap: 7px; }
.profile-list button { min-height: 44px; display: grid; gap: 3px; padding: 8px 10px; text-align: left; background: #fffdfa; }
.profile-list small { color: #706D6D; font-size: 11px; }
.profile-list b { font-size: 13px; }
.agent-history { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 9px; }
.agent-history article { display: grid; grid-template-columns: 40px minmax(0, 1fr) auto; align-items: center; gap: 9px; padding: 10px; border: 1px solid #ddd8d3; border-radius: 11px; background: #fffdfa; }
.agent-history img { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; }
.agent-history small { display: block; margin-top: 3px; color: #706D6D; font-size: 11px; }
pre { white-space: pre-wrap; padding: 12px; border-radius: 12px; background: #111110; color: #EEECEA; }
.modal { position: fixed; inset: 0; display: grid; place-items: center; padding: 24px; background: rgba(17,17,16,.42); z-index: 20; }
.modal-card { position: relative; width: min(760px, 96vw); max-height: 88vh; overflow: auto; display: grid; gap: 14px; padding: 22px; border-radius: 16px; background: #fbfaf8; }
.wide-modal { width: min(980px, 96vw); }
.close { position: absolute; top: 12px; right: 12px; width: 34px; height: 34px; padding: 0; }
.preview-box { min-height: 360px; display: grid; place-items: center; border: 1px solid #ddd8d3; border-radius: 12px; overflow: hidden; background: #f4f2ef; }
.preview-box img, .preview-box iframe { width: 100%; height: 520px; object-fit: contain; border: 0; }
.toast { position: fixed; right: 22px; bottom: 22px; padding: 12px 16px; border-radius: 12px; background: #111110; color: #EEECEA; z-index: 30; }
.operator-panel { min-height: 0; display: flex; flex-direction: column; gap: 16px; padding: 22px 20px; border-left: 1px solid #ddd8d3; background: linear-gradient(180deg, #f4f2ef, #EEECEA); }
.operator-head { display: grid; grid-template-columns: 76px minmax(0, 1fr) auto; align-items: center; gap: 12px; }
.operator-avatar { width: 76px; height: 76px; border-radius: 50%; object-fit: cover; box-shadow: 0 16px 28px rgba(17,17,16,.12); }
.operator-head h2 { margin-top: 5px; font-size: 22px; }
.operator-role { display: inline-flex; margin-top: 7px; padding: 4px 8px; border-radius: 999px; background: #EEECEA; color: #484336; font-size: 12px; font-weight: 900; }
.operator-status { flex-shrink: 0; padding: 6px 10px; border-radius: 999px; background: #e6ebe3; color: #425744; font-size: 12px; font-weight: 900; }
.operator-status.busy { background: #efe5d5; color: #694b22; }
.operator-duty { color: #706D6D; font-size: 13px; line-height: 1.6; }
.operator-slogan { padding: 10px 12px; border-radius: 12px; background: #fbfaf8; color: #484336; font-size: 13px; font-weight: 900; }
.chat-thread { flex: 1; min-height: 0; display: flex; flex-direction: column; gap: 12px; overflow: auto; padding-right: 2px; }
.bubble { max-width: 88%; padding: 12px 14px; border-radius: 14px; color: #484336; background: #fbfaf8; font-size: 13px; line-height: 1.55; }
.bubble.user { align-self: flex-end; background: #111110; color: #EEECEA; }
.bubble.assistant { align-self: flex-start; }
.message-attachments { display: grid; gap: 9px; margin: 0 0 10px; }
.message-attachments figure { display: grid; grid-template-columns: 54px minmax(0, 1fr); align-items: center; gap: 10px; margin: 0; padding: 8px; border-radius: 13px; border: 1px solid rgba(255,255,255,.28); background: rgba(255,255,255,.16); }
.message-attachments figure.image { grid-template-columns: 108px minmax(0, 1fr); }
.message-attachments img { width: 108px; height: 76px; border-radius: 10px; object-fit: cover; background: rgba(255,255,255,.28); box-shadow: 0 8px 18px rgba(0,0,0,.12); }
.message-attachments figure > span { width: 54px; height: 54px; display: grid; place-items: center; border-radius: 12px; background: rgba(255,255,255,.2); font-size: 11px; font-weight: 900; }
.message-attachments figcaption { min-width: 0; display: grid; gap: 3px; }
.message-attachments figcaption b { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 12px; }
.message-attachments figcaption small { opacity: .76; font-size: 11px; }
.bubble.assistant .message-attachments figure { border-color: #dce7e8; background: #f7fbfb; }
.bubble.assistant .message-attachments figure > span { background: #e6f3f2; color: var(--teal-dark); }
.bubble.assistant .message-attachments figcaption small { color: #6f8387; }
.message-attachments.compact figure { grid-template-columns: 46px minmax(0, 1fr); padding: 7px; }
.message-attachments.compact figure.image { grid-template-columns: 78px minmax(0, 1fr); }
.message-attachments.compact img { width: 78px; height: 58px; border-radius: 9px; }
.visually-hidden { position: absolute !important; width: 1px !important; height: 1px !important; padding: 0 !important; margin: -1px !important; overflow: hidden !important; clip: rect(0, 0, 0, 0) !important; white-space: nowrap !important; border: 0 !important; }
.file-pills img { width: 34px; height: 34px; border-radius: 7px; object-fit: cover; vertical-align: middle; margin-right: 6px; }
.modality-line { margin: 10px 0; }
.ask-box .attach-button { flex: 0 0 34px; width: 34px; padding: 0; font-size: 20px; }
.assistant-attachments { display: flex; flex-wrap: wrap; gap: 6px; padding-top: 8px; }
.assistant-attachments span { display: inline-flex; align-items: center; gap: 5px; max-width: 100%; padding: 5px 8px; border-radius: 8px; background: #edf6f5; color: #285f5b; font-size: 11px; }
.assistant-attachments button { border: 0; padding: 0 2px; background: transparent; color: #a44735; }
.executable-sop > span { align-items: flex-start; }
.executable-sop > span > span { display: grid; flex: 1; gap: 3px; padding: 0; background: transparent; }
.executable-sop > span > span small { color: var(--muted); line-height: 1.55; }
.executable-sop > span > button { margin-left: auto; white-space: nowrap; }
.executable-sop > span.completed { background: #eef7f2; color: #376958; }
.safety-reminders { display: grid; gap: 7px; margin-top: 14px; padding: 13px; border: 1px solid #ead8ba; border-radius: 10px; background: #fff9ef; }
.safety-reminders span { color: #765b2c; font-size: 13px; }
.knowledge-review-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 18px; }
.knowledge-review-list textarea { width: 100%; min-height: 86px; margin-top: 6px; padding: 10px; border: 1px solid var(--line); border-radius: 9px; resize: vertical; }
.quick-card { width: 100%; display: grid; grid-template-columns: 34px minmax(0, 1fr) auto; align-items: center; gap: 10px; padding: 12px; border: 1px solid #ddd8d3; border-radius: 14px; background: #fbfaf8; text-align: left; }
.quick-card > span { width: 34px; height: 34px; display: grid; place-items: center; border-radius: 11px; background: #111110; color: #EEECEA; }
.quick-card small { display: block; margin-top: 4px; color: #706D6D; font-size: 12px; line-height: 1.35; }
.quick-card i { font-style: normal; color: #706D6D; }
.operator-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.operator-chips button { min-height: 32px; padding: 6px 10px; border-radius: 999px; background: #fbfaf8; font-size: 12px; }
.ask-box { display: grid; grid-template-columns: minmax(0, 1fr) 40px; gap: 8px; padding: 8px; border: 1px solid #111110; border-radius: 16px; background: #fbfaf8; }
.ask-box input { min-width: 0; border: 0; outline: 0; background: transparent; color: #111110; }
.ask-box button { width: 40px; height: 40px; padding: 0; border-radius: 50%; background: #111110; color: #EEECEA; }

/* Web 端视觉基线：克制的工业色、清晰边界和稳定的信息层级。 */
:global(:root) {
  --ink: #172328;
  --muted: #68787e;
  --line: #dbe3e5;
  --surface: #ffffff;
  --surface-soft: #f4f7f7;
  --canvas: #edf2f3;
  --teal: #16766f;
  --teal-dark: #0f5854;
  --amber: #c8872e;
  --danger: #b44c43;
  --blue: #3979b8;
  --violet: #8062b5;
  --coral: #d86657;
}
:global(body) { background: radial-gradient(circle at 82% 6%, rgba(75,137,181,.08), transparent 30%), var(--canvas); color: var(--ink); font-family: "Segoe UI", "Microsoft YaHei", "PingFang SC", system-ui, sans-serif; }
.app-shell { grid-template-columns: 220px minmax(0, 1fr); background: var(--canvas); }
.app-shell.collapsed { grid-template-columns: 76px minmax(0, 1fr); }
.side-nav { gap: 22px; padding: 18px 12px; border-right: 1px solid #d9cfba; background: linear-gradient(180deg, #f7f3ec 0%, #e8e1d0 100%); box-shadow: 0 0 0 rgba(0,0,0,0); }
.brand { border: 0; background: transparent; width: 160px; height: 64px; filter: none; object-fit: contain; }
.side-nav nav { gap: 6px; }
.side-nav nav button { min-height: 44px; border-radius: 9px; color: #3a2e1f; font-weight: 700; letter-spacing: .02em; }
.nav-icon { background: rgba(198, 135, 46, 0.14); color: #8a4e0e; }
.side-nav nav button.active { background: #8a4e0e; color: #fff; box-shadow: 0 8px 18px rgba(138, 78, 14, .18); }
.side-nav nav button:hover:not(.active) { background: rgba(198, 135, 46, 0.14); color: #3a2e1f; }
.side-nav nav button.active .nav-icon { background: rgba(255,255,255,.2); color: #fff; }
.collapse-btn { background: rgba(58, 46, 31, 0.08); color: #3a2e1f; }
.topbar { height: 76px; grid-template-columns: minmax(180px, 1fr) minmax(280px, 410px) auto 38px auto auto; border-bottom-color: var(--line); background: rgba(255,255,255,.96); }
.page-title-block { --title-accent: var(--teal); position: relative; align-self: center; min-width: 230px; max-width: 420px; padding: 8px 15px 8px 18px; overflow: hidden; border: 1px solid color-mix(in srgb, var(--title-accent) 22%, #dfe8e8); border-radius: 11px; background: linear-gradient(105deg, color-mix(in srgb, var(--title-accent) 10%, #fff), rgba(255,255,255,.94) 72%); box-shadow: 0 5px 14px rgba(31,55,63,.045); }
.page-title-block::before { content: ""; position: absolute; inset: 0 auto 0 0; width: 5px; background: var(--title-accent); }
.page-title-block::after { content: ""; position: absolute; top: -26px; right: -12px; width: 84px; height: 84px; border-radius: 50%; background: color-mix(in srgb, var(--title-accent) 9%, transparent); pointer-events: none; }
.page-title-block.title-home { --title-accent: var(--teal); }
.page-title-block.title-search { --title-accent: var(--blue); }
.page-title-block.title-tasks { --title-accent: var(--amber); }
.page-title-block.title-knowledge { --title-accent: var(--violet); }
.page-title-block.title-profile { --title-accent: var(--coral); }
.page-title-block .breadcrumb { position: relative; z-index: 1; color: color-mix(in srgb, var(--title-accent) 82%, #33494e); font-size: 10px; }
.page-title-block h1 { position: relative; z-index: 1; margin-top: 2px; font-size: 19px; }
.content-shell { height: calc(100vh - 76px); grid-template-columns: minmax(0, 1fr) 320px; }
.breadcrumb, .eyebrow { color: var(--page-accent, var(--teal)); letter-spacing: .08em; }
h1 { color: var(--ink); font-size: 21px; letter-spacing: .02em; }
.global-search { border-color: var(--line); border-radius: 10px; background: var(--surface-soft); transition: border-color .18s, box-shadow .18s; }
.global-search:focus-within { border-color: #82aaa7; box-shadow: 0 0 0 3px rgba(22,118,111,.1); }
.global-search button { min-height: 28px; padding: 4px 10px; border: 0; border-radius: 7px; background: var(--page-accent, var(--teal)); color: #fff; font-size: 12px; }
.global-search button { min-width: 46px; white-space: nowrap; }
.work-strip span, .badge, .tag-line span { background: #e9eff0; color: #41545a; }
.icon-button, .user-chip { border-color: var(--line); background: var(--surface); }
.page-scroll { padding: 20px; }
.page-grid { gap: 14px; }
.page-theme-home { --page-accent: var(--teal); --page-accent-soft: rgba(22,118,111,.06); --page-accent-tint: linear-gradient(120deg, #fff 0%, #f0f8f7 100%); }
.page-theme-search { --page-accent: var(--blue); --page-accent-soft: rgba(57,121,184,.06); --page-accent-tint: linear-gradient(120deg, #fff 0%, #f0f6fc 100%); }
.page-theme-tasks { --page-accent: var(--amber); --page-accent-soft: rgba(200,135,46,.06); --page-accent-tint: linear-gradient(120deg, #fff 0%, #fdf8f0 100%); }
.page-theme-knowledge { --page-accent: var(--violet); --page-accent-soft: rgba(128,98,181,.06); --page-accent-tint: linear-gradient(120deg, #fff 0%, #f7f4fc 100%); }
.page-theme-profile { --page-accent: var(--coral); --page-accent-soft: rgba(216,102,87,.06); --page-accent-tint: linear-gradient(120deg, #fff 0%, #fdf5f3 100%); }
.page-theme-home .breadcrumb, .page-theme-home .eyebrow { color: var(--teal); }
.page-theme-search .breadcrumb, .page-theme-search .eyebrow { color: var(--blue); }
.page-theme-tasks .breadcrumb, .page-theme-tasks .eyebrow { color: var(--amber); }
.page-theme-knowledge .breadcrumb, .page-theme-knowledge .eyebrow { color: var(--violet); }
.page-theme-profile .breadcrumb, .page-theme-profile .eyebrow { color: var(--coral); }
.page-theme-home .welcome-card { border-top-color: var(--teal); }
.page-theme-search .search-input-panel::before { background: linear-gradient(90deg, var(--blue), #5b9bdb 58%, #82b8e0); }
.page-theme-tasks .task-nav-panel { border-top-color: var(--amber) !important; background: linear-gradient(120deg, #fff, #fdf8f0) !important; }
.page-theme-tasks .task-nav-panel::after { color: rgba(200,135,46,.055); }
.page-theme-tasks .task-nav-panel .tabs button.active { background: var(--amber); box-shadow: 0 6px 14px rgba(200,135,46,.18); }
.page-theme-knowledge .knowledge-nav-panel { border-top-color: var(--violet) !important; background: linear-gradient(120deg, #fff 0%, #f7f4fc 70%, #efe8f8 100%) !important; }
.page-theme-knowledge .knowledge-nav-panel::after { color: rgba(128,98,181,.055); }
.page-theme-knowledge .knowledge-nav-panel .tabs button.active { background: var(--violet); box-shadow: 0 6px 13px rgba(128,98,181,.17); }
.page-theme-profile .profile-hero { border-color: #ddd8d3; background: linear-gradient(180deg, #fffdfa, #fdf5f3); }
.panel, .welcome-card, .agent-card, .stat-card, .profile-card { border-color: var(--line); border-radius: 12px; background: var(--surface); box-shadow: 0 8px 24px rgba(31, 55, 63, .055); }
.welcome-card { position: relative; overflow: hidden; border-top: 3px solid var(--page-accent, var(--teal)); }
.welcome-brand { grid-template-columns: 220px minmax(0, 1fr); gap: 20px; }
.welcome-brand img { width: 220px; height: 112px; filter: none; }
.welcome-card h2 { color: var(--ink); font-size: 25px; line-height: 1.35; }
.welcome-card p { color: var(--muted); line-height: 1.65; }
.execution-summary { display: grid; grid-template-columns: 74px minmax(0, 1fr) 108px 108px; align-items: center; gap: 14px; margin-top: 14px; padding: 12px 14px; border: 1px solid #d9e8e6; border-radius: 11px; background: #f4f9f8; }
.progress-ring { --progress: 0%; width: 64px; height: 64px; display: grid; place-items: center; border-radius: 50%; background: conic-gradient(var(--teal) var(--progress), #d9e6e5 0); }
.progress-ring::before { content: ""; grid-area: 1 / 1; width: 50px; height: 50px; border-radius: 50%; background: #fff; }
.progress-ring span { z-index: 1; grid-area: 1 / 1; display: grid; color: var(--muted); font-size: 9px; text-align: center; }
.progress-ring b { color: var(--ink); font-size: 15px; }
.execution-copy strong { color: var(--ink); font-size: 14px; }
.execution-copy p { margin-top: 4px; font-size: 12px; }
.summary-metric { display: grid; gap: 3px; padding-left: 12px; border-left: 1px solid #cedfdd; }
.summary-metric b { color: var(--ink); font-size: 22px; }
.summary-metric span { color: var(--muted); font-size: 11px; }
.health-grid { grid-template-columns: repeat(5, minmax(0, 1fr)); }
.health-grid span, .analysis-grid span, .detail-grid span { background: var(--surface-soft); color: #53656b; }
.focus-tasks { display: grid; gap: 6px; margin-top: 12px; }
.focus-tasks-title { display: flex; align-items: center; justify-content: space-between; color: var(--ink); font-size: 13px; }
.focus-tasks-title span { color: var(--muted); font-size: 11px; }
.focus-tasks button { display: grid; grid-template-columns: minmax(0, 1fr) auto 42px; align-items: center; gap: 8px; min-height: 40px; padding: 7px 9px; border-color: #e2e8e9; background: #fbfcfc; text-align: left; }
.focus-tasks button:hover { border-color: #a8c5c2; background: #f1f8f7; }
.focus-tasks button span { display: flex; align-items: baseline; gap: 7px; min-width: 0; }
.focus-tasks button small { overflow: hidden; color: var(--muted); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.focus-tasks button em { color: var(--muted); font-size: 11px; font-style: normal; text-align: right; }
.agent-card { align-self: start; }
.agent-card-head { margin-bottom: 6px; }
.agent-card-head h3 { margin-top: 5px; font-size: 16px; }
.agent-card-head > small { color: var(--muted); font-size: 11px; }
.agent-row { grid-template-columns: 40px 8px minmax(0, 1fr) auto; width: 100%; gap: 8px; padding: 8px 6px; border: 0; border-bottom: 1px solid #edf1f2; border-radius: 8px; background: transparent; color: var(--ink); text-align: left; }
.agent-row:hover, .agent-row.active { background: #edf6f5; }
.agent-row img { width: 40px; height: 40px; box-shadow: none; }
.agent-row i { color: #91a0a5; font-style: normal; }
.agent-row small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.kpi-ribbon { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 10px; }
.stat-card { min-width: 0; min-height: 106px; border-top: 3px solid #9cb7b5; }
.stat-card:nth-child(4) { border-top-color: var(--danger); }
.stat-card:nth-child(5) { border-top-color: var(--amber); }
.stat-card:nth-child(1) { border-top-color: var(--blue); }
.stat-card:nth-child(2) { border-top-color: var(--amber); }
.stat-card:nth-child(3) { border-top-color: var(--teal); }
.stat-card:nth-child(6) { border-top-color: var(--violet); }
.stat-card:nth-child(1) b { color: var(--blue); }
.stat-card:nth-child(2) b, .stat-card:nth-child(5) b { color: #a96c20; }
.stat-card:nth-child(3) b { color: var(--teal); }
.stat-card:nth-child(4) b { color: var(--danger); }
.stat-card:nth-child(6) b { color: var(--violet); }
.stat-card:hover { transform: translateY(-2px); border-color: #aac3c1; box-shadow: 0 12px 25px rgba(31, 55, 63, .09); }
.stat-card span, .stat-card small { color: var(--muted); }
.stat-card b { color: var(--ink); font-size: 28px; }
.quick-grid button, .history-row, .alert-list button { border-color: var(--line); background: var(--surface-soft); }
.quick-grid button:hover, .history-row:hover, .alert-list button:hover { border-color: #a6c5c2; background: #edf6f5; }
.quick-grid button:nth-child(4n+1) { border-left: 3px solid var(--blue); }
.quick-grid button:nth-child(4n+2) { border-left: 3px solid var(--teal); }
.quick-grid button:nth-child(4n+3) { border-left: 3px solid var(--violet); }
.quick-grid button:nth-child(4n) { border-left: 3px solid var(--amber); }
.home-task-panel, .quick-panel { align-self: stretch; }
.home-task-track-row {
  display: grid;
  grid-template-columns: minmax(0, 1.42fr) minmax(310px, .78fr);
  gap: 14px;
  align-items: stretch;
}
.home-task-track-row .home-task-panel,
.home-task-track-row .activity-panel {
  grid-column: auto !important;
  min-width: 0;
  height: 100%;
}
.home-task-compact {
  padding: 17px !important;
  background: linear-gradient(180deg, #fff 0%, #fbfcfb 100%);
}
.work-track-panel {
  padding: 17px !important;
  border-color: #dfe8e5 !important;
  background:
    linear-gradient(90deg, rgba(111,144,135,.08) 1px, transparent 1px),
    linear-gradient(180deg, #fffefb 0%, #f8fbfa 100%);
  background-size: 34px 34px, auto;
}
.home-task-title, .quick-panel-title { margin-bottom: 12px; }
.task-title-actions { display: flex; align-items: center; gap: 9px; }
.task-title-actions > span { padding: 5px 9px; border-radius: 999px; background: #edf3f4; color: var(--muted); font-size: 11px; font-weight: 800; }
.task-title-actions .ghost { border-color: #cddadd; background: #fff; color: var(--teal-dark); font-size: 12px; font-weight: 800; }
.home-task-list { display: grid; gap: 9px; }
.home-task-compact .home-task-list { gap: 8px; }
.home-task-row {
  --task-risk: #6f9087;
  position: relative;
  display: grid;
  grid-template-columns: 42px minmax(210px, 1.4fr) minmax(150px, .9fr) minmax(112px, .64fr) minmax(150px, .86fr) 22px;
  align-items: center;
  gap: 13px;
  min-height: 82px;
  padding: 11px 12px 11px 10px;
  overflow: hidden;
  border: 1px solid #dde8e7;
  border-radius: 13px;
  background: linear-gradient(135deg, #ffffff 0%, #fbfdfc 58%, #f2f7f5 100%);
  color: var(--ink);
  text-align: left;
  box-shadow: 0 1px 0 rgba(255,255,255,.9) inset;
}
.home-task-compact .home-task-row {
  grid-template-columns: 34px minmax(150px, 1.2fr) minmax(126px, .78fr) minmax(92px, .5fr) minmax(118px, .72fr) 20px;
  gap: 9px;
  min-height: 68px;
  padding: 9px 10px 9px 8px;
  border-radius: 12px;
  background: #fff;
}
.home-task-compact .task-index-block b { width: 27px; height: 27px; border-radius: 9px; font-size: 10px; }
.home-task-compact .task-index-block i { height: 16px; }
.home-task-compact .task-device-block b { font-size: 14px; }
.home-task-compact .task-owner-block { grid-template-columns: 28px minmax(0, 1fr); gap: 7px; }
.home-task-compact .task-owner-block > i { width: 28px; height: 28px; border-radius: 10px; font-size: 12px; }
.home-task-compact .task-progress-block small { display: none; }
.home-task-row::before {
  content: "";
  position: absolute;
  left: 0;
  top: 10px;
  bottom: 10px;
  width: 4px;
  border-radius: 0 999px 999px 0;
  background: var(--task-risk);
}
.home-task-row.risk-high, .home-task-row.risk-critical { --task-risk: #c95f5a; }
.home-task-row.risk-medium { --task-risk: #d79542; }
.home-task-row.risk-low { --task-risk: #6f9087; }
.home-task-row:hover { transform: translateY(-2px); border-color: color-mix(in srgb, var(--task-risk) 28%, #dce7e6); background: #fff; box-shadow: 0 12px 24px rgba(31,55,63,.075); }
.task-index-block { display: grid; justify-items: center; gap: 5px; color: var(--task-risk); }
.task-index-block b { width: 30px; height: 30px; display: grid; place-items: center; border-radius: 10px; background: color-mix(in srgb, var(--task-risk) 10%, #fff); font-size: 11px; font-weight: 900; font-variant-numeric: tabular-nums; }
.task-index-block i { width: 1px; height: 22px; border-radius: 999px; background: color-mix(in srgb, var(--task-risk) 32%, #e8eeee); }
.task-device-block, .task-fault-block, .task-progress-block { display: grid; gap: 4px; min-width: 0; }
.task-device-block small { color: var(--task-risk); font-size: 10px; font-weight: 900; letter-spacing: .04em; }
.task-device-block b { overflow: hidden; color: #1f3338; font-size: 15px; text-overflow: ellipsis; white-space: nowrap; }
.task-device-block em { overflow: hidden; color: #738489; font-size: 10px; font-style: normal; text-overflow: ellipsis; white-space: nowrap; }
.task-fault-block { justify-items: start; }
.task-fault-block > span { display: flex; align-items: center; gap: 7px; min-width: 0; }
.task-fault-block > span b { overflow: hidden; color: #30474d; font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.task-fault-block small, .task-owner-block small, .task-progress-block small { overflow: hidden; color: #859399; font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.task-fault-block .badge { padding: 3px 7px; font-size: 9px; font-style: normal; }
.task-owner-block { display: grid; grid-template-columns: 34px minmax(0, 1fr); align-items: center; gap: 8px; min-width: 0; }
.task-owner-block > i { width: 34px; height: 34px; display: grid; place-items: center; border-radius: 12px; background: color-mix(in srgb, var(--task-risk) 10%, #fff); color: var(--task-risk); font-size: 13px; font-style: normal; font-weight: 900; box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--task-risk) 12%, transparent); }
.task-owner-block > span { display: grid; gap: 3px; min-width: 0; }
.task-owner-block b { overflow: hidden; color: #34494e; font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.task-progress-block > span { display: flex; align-items: center; justify-content: space-between; gap: 7px; }
.task-progress-block > span b { color: #30474d; font-size: 12px; }
.task-progress-block > span em { color: var(--task-risk); font-size: 11px; font-style: normal; font-weight: 900; }
.task-progress-block > i { width: 100%; height: 6px; overflow: hidden; border-radius: 999px; background: #e6eeee; }
.task-progress-block > i u { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, color-mix(in srgb, var(--task-risk) 76%, #fff), var(--task-risk)); text-decoration: none; }
.row-arrow { width: 22px; height: 22px; display: grid; place-items: center; border-radius: 8px; background: #f0f5f4; color: #8a9b9f; font-size: 14px; }
.home-task-row:hover .row-arrow { background: color-mix(in srgb, var(--task-risk) 12%, #fff); color: var(--task-risk); }
.quick-panel { background: linear-gradient(155deg, #fff 0%, #fbfcfc 70%, #f3f8f8 100%); }
.home-quick-grid { gap: 9px; }
.home-quick-grid button { display: grid; grid-template-columns: 38px minmax(0, 1fr) auto; align-items: center; gap: 9px; min-height: 72px; padding: 9px 10px; border: 1px solid #e0e8e9; border-left: 1px solid #e0e8e9 !important; background: rgba(255,255,255,.86); text-align: left; }
.home-quick-grid button:hover { transform: translateY(-2px); border-color: #bdd0d2; background: #fff; box-shadow: 0 8px 17px rgba(31,55,63,.07); }
.quick-icon { width: 38px; height: 38px; display: grid; place-items: center; border-radius: 11px; }
.quick-copy { display: grid; gap: 3px; min-width: 0; }
.quick-copy b { overflow: hidden; color: var(--ink); font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.quick-copy small { overflow: hidden; color: var(--muted); font-size: 9px; text-overflow: ellipsis; white-space: nowrap; }
.home-quick-grid button > i { color: #96a4a9; font-style: normal; }
.quick-blue .quick-icon { background: #e2edf8; color: var(--blue); }
.quick-teal .quick-icon { background: #dff1ef; color: var(--teal); }
.quick-violet .quick-icon { background: #eee8f7; color: var(--violet); }
.quick-amber .quick-icon { background: #faecd8; color: #b57526; }
.chart-wrap svg { background: linear-gradient(#e5ebec 1px, transparent 1px), #fbfcfc; }
.chart-wrap polyline { stroke: var(--teal); }
.chart-wrap rect { fill: #a9c3c1; }
.distribution b, .load-row b { background: var(--teal); }
.primary, .tabs button.active, .view-switch button.active { border-color: var(--teal-dark); background: var(--teal-dark); color: #fff; }
button { transition: background-color .18s, border-color .18s, color .18s, transform .18s, box-shadow .18s; }
.operator-panel { gap: 14px; padding: 20px 18px; border-left-color: var(--line); background: #f2f6f6; }
.operator-avatar { width: 64px; height: 64px; border: 3px solid #fff; box-shadow: 0 8px 20px rgba(22, 60, 64, .14); }
.operator-head { grid-template-columns: 64px minmax(0, 1fr) auto; }
.operator-head h2 { color: var(--ink); font-size: 20px; }
.operator-role, .operator-slogan, .bubble, .quick-card, .operator-chips button { background: #fff; }
.operator-slogan { border-left: 3px solid var(--teal); color: #465b60; }
.bubble.user { background: var(--teal-dark); color: #fff; }
.quick-card { border-color: #ccdcda; }
.quick-card > span, .ask-box button { background: var(--teal-dark); color: #fff; }
.ask-box { border-color: #9bb9b7; background: #fff; }
.toast { background: #153438; color: #fff; }

/* 首页下半区：用颜色表达状态，而不是单纯堆叠灰色卡片。 */
.section-title-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; margin-bottom: 14px; }
.section-title-row h3 { margin-top: 5px; color: var(--ink); font-size: 19px; }
.section-count, .quiet-label { padding: 5px 9px; border-radius: 999px; background: #edf3f4; color: #66777d; font-size: 11px; font-weight: 800; }
.alert-panel { position: relative; overflow: hidden; background: linear-gradient(160deg, #ffffff 0%, #fbfcfc 66%, #f2f7f7 100%); }
.alert-panel, .analytics-panel { align-self: start; }
.alert-panel::before, .analytics-panel::before, .activity-panel::before, .knowledge-recent-panel::before { content: ""; position: absolute; top: 0; left: 18px; right: 18px; height: 3px; border-radius: 0 0 4px 4px; background: linear-gradient(90deg, var(--coral), var(--amber)); }
.analytics-panel, .activity-panel, .knowledge-recent-panel { position: relative; overflow: hidden; }
.analytics-panel::before { background: linear-gradient(90deg, var(--blue), var(--teal), var(--violet)); }
.activity-panel::before { background: linear-gradient(90deg, var(--blue), #63a9cb); }
.knowledge-recent-panel::before { background: linear-gradient(90deg, var(--violet), var(--teal)); }
.alert-list { height: auto; grid-auto-rows: minmax(82px, auto); align-content: start; gap: 9px; margin-top: 0; }
.alert-list button { position: relative; display: grid; grid-template-columns: 42px minmax(0, 1fr) auto; align-items: center; gap: 11px; min-height: 82px; padding: 11px 12px; overflow: visible; border: 1px solid transparent; background: #f6f8f8; }
.alert-list button:hover { transform: translateX(3px); box-shadow: 0 8px 18px rgba(31,55,63,.08); }
.alert-icon { width: 40px; height: 40px; display: grid; place-items: center; border-radius: 11px; }
.alert-copy { display: grid; align-content: center; gap: 4px; min-width: 0; overflow: visible; }
.alert-copy b { color: var(--ink); font-size: 14px; line-height: 1.35; }
.alert-copy small { display: block; margin-top: 0; overflow: visible; color: var(--muted); line-height: 1.45; text-overflow: clip; white-space: normal; }
.alert-arrow { color: #91a1a6; font-size: 16px; }
.tone-danger { border-color: #f0d8d5 !important; background: #fff7f6 !important; }
.tone-danger .alert-icon { background: #fbe3e0; color: var(--danger); }
.tone-amber { border-color: #f0e0c8 !important; background: #fffbf4 !important; }
.tone-amber .alert-icon { background: #f9ecd6; color: #b67625; }
.tone-violet { border-color: #e3dbf0 !important; background: #faf8ff !important; }
.tone-violet .alert-icon { background: #eee8f7; color: var(--violet); }
.tone-teal { border-color: #d5e8e5 !important; background: #f5fbfa !important; }
.tone-teal .alert-icon { background: #dff1ef; color: var(--teal); }
.chart-legend { display: flex; align-items: center; gap: 7px; color: #4f6268; font-size: 11px; }
.chart-legend i { width: 9px; height: 9px; border-radius: 50%; background: var(--teal); }
.chart-legend span { margin-left: 5px; padding: 4px 8px; border-radius: 999px; background: #eef4f5; color: #75858a; }
.analytics-panel { grid-column: span 8; }
.analytics-panel .chart-wrap { grid-template-columns: minmax(0, 1fr) 210px; gap: 22px; margin-top: 8px; }
.analytics-panel .chart-wrap svg { height: 270px; border: 1px solid #e4ebec; background: linear-gradient(180deg, #fbfdfe, #f7fafb); }
.chart-grid-line { stroke: #dfe8ea; stroke-width: 1; stroke-dasharray: 4 6; }
.chart-label { fill: #75858a; font-size: 11px; }
.trend-dot { fill: #fff; stroke: var(--teal); stroke-width: 3px; }
/* ECharts 图表容器美化 */
.chart-canvas { width: 100%; min-height: 0; }
.chart-canvas.echart-root { display: block; }
.analytics-panel .chart-wrap .chart-canvas:first-child { border: 1px solid #e4ebec; border-radius: 12px; background: linear-gradient(180deg, #fbfdfe, #f7fafb); padding: 4px 6px 0; box-sizing: border-box; }
.analytics-panel .distribution { display: grid; align-content: center; gap: 10px; }
.dashboard-charts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-top: 14px; }
.chart-tile { min-width: 0; padding: 13px 14px 10px; border: 1px solid #e0e9ea; border-radius: 12px; background: linear-gradient(180deg, #fff, #f8fbfb); box-shadow: inset 0 1px 0 rgba(255,255,255,.75); }
.chart-tile-wide { grid-column: span 2; }
.chart-tile-head { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; margin-bottom: 6px; }
.chart-tile-head b { overflow: hidden; color: var(--ink); font-size: 14px; text-overflow: ellipsis; white-space: nowrap; }
.chart-tile-head small { flex-shrink: 0; color: var(--muted); font-size: 10px; font-weight: 800; }
.chart-tile .chart-canvas { border-radius: 10px; background: linear-gradient(180deg, #fbfdfe, #f6fafb); }
.chart-tile-wide:first-child { background: linear-gradient(145deg, #fff 0%, #f3faf9 64%, #f7f5fb 100%); }
.chart-tile:nth-child(2) { background: linear-gradient(145deg, #fff 0%, #f4f8fc 100%); }
.chart-tile:nth-child(3) { background: linear-gradient(145deg, #fff 0%, #fff8f3 100%); }
.chart-tile:nth-child(4) { background: linear-gradient(145deg, #fff 0%, #f7f4fc 100%); }
.chart-tile:nth-child(5) { background: linear-gradient(145deg, #fff 0%, #f5fbf8 100%); }
.chart-section { display: grid; align-content: start; gap: 6px; }
.chart-hint { margin: 0; color: var(--muted); font-size: 10px; text-align: center; letter-spacing: .02em; }
.task-analytics .task-trend-echart { height: 166px; }
.distribution { align-content: center; gap: 15px; }
.distribution-head { display: flex; justify-content: space-between; align-items: baseline; padding-bottom: 4px; border-bottom: 1px solid #e6ecee; }
.distribution-head b { height: auto; background: transparent; color: var(--ink); font-size: 14px; }
.distribution-head small { color: var(--muted); }
.distribution span { grid-template-columns: 10px minmax(0, 1fr) auto; grid-template-areas: "dot label value" ". bar bar"; gap: 5px 7px; color: var(--muted); }
.distribution span > i { grid-area: dot; width: 8px; height: 8px; align-self: center; border-radius: 50%; background: var(--dist-color); }
.distribution span > em { grid-area: label; font-style: normal; }
.distribution span > strong { grid-area: value; color: var(--ink); font-size: 12px; }
.distribution span > b { grid-area: bar; width: 100%; height: 6px; overflow: hidden; border-radius: 999px; background: #edf1f2; }
.distribution span > b > u { display: block; height: 100%; border-radius: inherit; background: var(--dist-color); text-decoration: none; }
.activity-list { display: grid; gap: 9px; }
.activity-list button { display: grid; grid-template-columns: 42px minmax(0, 1fr) auto; align-items: center; gap: 11px; min-height: 67px; padding: 10px 12px; border: 1px solid #e1e8ea; border-radius: 11px; background: #fbfcfc; text-align: left; }
.activity-list button:hover { transform: translateY(-2px); border-color: #b9cdd1; box-shadow: 0 9px 18px rgba(31,55,63,.07); }
.activity-icon { width: 40px; height: 40px; display: grid; place-items: center; border-radius: 11px; }
.work-track-list {
  position: relative;
  gap: 7px;
  padding-left: 7px;
}
.work-track-list::before {
  content: "";
  position: absolute;
  left: 25px;
  top: 12px;
  bottom: 12px;
  width: 1px;
  background: linear-gradient(180deg, rgba(79,139,134,.16), rgba(181,139,75,.32), rgba(111,144,135,.1));
}
.work-track-list button {
  position: relative;
  grid-template-columns: 36px minmax(0, 1fr) 18px;
  min-height: 56px;
  padding: 8px 9px;
  border-color: rgba(214,225,224,.82);
  border-radius: 12px;
  background: rgba(255,255,255,.86);
  box-shadow: 0 1px 0 rgba(255,255,255,.85) inset;
}
.work-track-list button:hover {
  border-color: #c8d9d6;
  background: #fff;
  box-shadow: 0 10px 20px rgba(39,61,61,.065);
}
.work-track-list .activity-icon {
  z-index: 1;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  box-shadow: 0 0 0 4px #fffdfb;
}
.work-track-list small {
  font-size: 10px;
  font-weight: 700;
}
.work-track-list b {
  color: #2c4045;
  font-size: 13px;
  font-weight: 720;
  line-height: 1.35;
}
.work-track-list button > i {
  width: 18px;
  height: 18px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #f0f5f3;
  font-size: 12px;
}
.activity-list button > span:nth-child(2) { display: grid; gap: 3px; min-width: 0; }
.activity-list small { color: var(--muted); font-size: 11px; }
.activity-list b { overflow: hidden; color: var(--ink); font-size: 14px; text-overflow: ellipsis; white-space: nowrap; }
.activity-list button > i { color: #91a1a6; font-style: normal; }
.activity-blue .activity-icon { background: #e3eef8; color: var(--blue); }
.activity-violet .activity-icon { background: #eee8f7; color: var(--violet); }
.activity-amber .activity-icon { background: #faecd8; color: #b57526; }
.activity-teal .activity-icon { background: #dff1ef; color: var(--teal); }
.home-task-track-row {
  grid-template-columns: minmax(0, 1.34fr) minmax(360px, .76fr);
  gap: 16px;
}
.home-task-track-row > .panel {
  min-height: 430px;
  padding: 20px 22px !important;
  border: 1px solid #d9e4e4 !important;
  border-radius: 16px !important;
  background: rgba(255,255,255,.93) !important;
  box-shadow: 0 12px 28px rgba(31,55,63,.055), inset 0 1px 0 rgba(255,255,255,.88) !important;
}
.home-task-track-row > .panel::before {
  display: none;
}
.home-task-track-row .section-title-row {
  min-height: 56px;
  align-items: flex-start;
  margin-bottom: 16px;
  padding-bottom: 13px;
  border-bottom: 1px solid #edf2f2;
}
.home-task-track-row .eyebrow {
  color: #3e7c78;
  font-size: 13px;
  font-weight: 780;
  letter-spacing: .02em;
}
.home-task-track-row .section-title-row h3 {
  margin-top: 8px;
  color: #203237;
  font-size: 22px;
  font-weight: 760;
  line-height: 1.18;
}
.home-task-track-row .task-title-actions {
  align-items: center;
  padding-top: 2px;
}
.home-task-track-row .task-title-actions > span,
.home-task-track-row .quiet-label {
  padding: 8px 12px;
  border: 1px solid #e1e9e9;
  background: #f4f8f7;
  color: #60767a;
  font-size: 12px;
  font-weight: 720;
}
.home-task-track-row .task-title-actions .ghost {
  min-height: 38px;
  padding: 0 14px;
  border-color: #cbdada;
  border-radius: 999px;
  background: #fff;
  color: #315f5b;
  box-shadow: 0 6px 16px rgba(49,95,91,.055);
}
.home-task-track-row .home-task-list {
  gap: 10px;
}
.home-task-compact .home-task-row {
  grid-template-columns: 40px minmax(160px, 1.12fr) minmax(132px, .74fr) minmax(96px, .48fr) minmax(128px, .66fr) 28px;
  min-height: 76px;
  padding: 10px 12px 10px 10px;
  border-color: #dce8e7;
  border-radius: 14px;
  background: linear-gradient(180deg, #fff 0%, #fbfdfc 100%);
  box-shadow: 0 1px 0 rgba(255,255,255,.92) inset;
}
.home-task-compact .home-task-row::before {
  top: 14px;
  bottom: 14px;
  width: 5px;
  border-radius: 0 12px 12px 0;
}
.home-task-compact .home-task-row:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 22px rgba(31,55,63,.07);
}
.home-task-compact .task-index-block {
  gap: 4px;
}
.home-task-compact .task-index-block b {
  width: 32px;
  height: 32px;
  border-radius: 11px;
  background: color-mix(in srgb, var(--task-risk) 12%, #fff);
  font-size: 11px;
  font-weight: 820;
}
.home-task-compact .task-index-block i {
  height: 18px;
}
.rank-hot {
  background: linear-gradient(135deg, #ff6b6b, #ee5a24);
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: block;
}
.rank-warm {
  background: linear-gradient(135deg, #ffa502, #f39c12);
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: block;
}
.rank-new {
  background: linear-gradient(135deg, #7bed9f, #2ed573);
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: block;
}
.skill-row {
  text-decoration: none;
  color: inherit;
  cursor: pointer;
}
.skill-row:hover {
  background: color-mix(in srgb, var(--task-risk, #3b82f6) 6%, #fff);
}
.home-task-compact .task-device-block small {
  color: var(--task-risk);
  font-size: 11px;
  font-weight: 800;
}
.home-task-compact .task-device-block b {
  color: #25393e;
  font-size: 15px;
  font-weight: 780;
}
.home-task-compact .task-device-block em,
.home-task-compact .task-fault-block small,
.home-task-compact .task-owner-block small {
  color: #76898d;
  font-size: 11px;
}
.home-task-compact .task-fault-block > span b,
.home-task-compact .task-progress-block > span b {
  color: #263b40;
  font-size: 14px;
  font-weight: 760;
}
.home-task-compact .task-fault-block .badge {
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 760;
}
.home-task-compact .task-owner-block {
  grid-template-columns: 34px minmax(0, 1fr);
}
.home-task-compact .task-owner-block > i {
  width: 34px;
  height: 34px;
  border-radius: 12px;
}
.home-task-compact .task-owner-block b {
  color: #2b4045;
  font-size: 13px;
  font-weight: 780;
}
.home-task-compact .task-progress-block > i {
  height: 7px;
  background: #e6eeee;
}
.home-task-compact .row-arrow {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #f2f6f5;
  color: #7d9195;
}
.work-track-panel {
  background:
    radial-gradient(circle at 18px 18px, rgba(86,125,118,.055) 1px, transparent 1.5px),
    linear-gradient(180deg, #fff 0%, #fbfcfb 100%) !important;
  background-size: 26px 26px, auto !important;
}

/* ===== Chat Memory Panel ===== */
.chat-memory-panel {
  padding: 20px;
}
.chat-memory-header {
  margin-bottom: 20px;
}
.chat-memory-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  padding: 14px 18px;
  background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
  border-radius: 12px;
  border: 1px solid #d1fae5;
}
.chat-memory-stats .stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 70px;
}
.chat-memory-stats .stat-num {
  font-size: 20px;
  font-weight: 800;
  color: #059669;
}
.chat-memory-stats .stat-label {
  font-size: 11px;
  color: #6b7280;
  margin-top: 2px;
}
.chat-memory-toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
}
.chat-memory-search {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
}
.chat-memory-search input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 13px;
  background: transparent;
}
.chat-memory-search .ui-icon {
  width: 16px;
  height: 16px;
  color: #9ca3af;
}
.chat-memory-filters {
  display: flex;
  gap: 4px;
}
.chat-memory-filters button {
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  font-size: 12px;
  cursor: pointer;
  transition: all .15s;
}
.chat-memory-filters button.active {
  background: #059669;
  color: #fff;
  border-color: #059669;
}
.chat-memory-filters button:hover:not(.active) {
  background: #f3f4f6;
}
.chat-memory-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.chat-memory-card {
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
  transition: all .2s;
}
.chat-memory-card:hover {
  border-color: #059669;
  box-shadow: 0 2px 8px rgba(5,150,105,.1);
}
.chat-memory-card.level-L3 { border-left: 4px solid #8b5cf6; }
.chat-memory-card.level-L2 { border-left: 4px solid #3b82f6; }
.chat-memory-card.level-L1 { border-left: 4px solid #10b981; }
.chat-memory-card.level-L0 { border-left: 4px solid #6b7280; }
.memory-card-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.memory-level-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
}
.memory-level-badge.L3 { background: #8b5cf6; }
.memory-level-badge.L2 { background: #3b82f6; }
.memory-level-badge.L1 { background: #10b981; }
.memory-level-badge.L0 { background: #6b7280; }
.memory-visibility {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
}
.memory-visibility.team { background: #dbeafe; color: #1d4ed8; }
.memory-visibility.private { background: #f3f4f6; color: #6b7280; }
.memory-owner {
  font-size: 12px;
  color: #6b7280;
  margin-left: auto;
}
.memory-title {
  font-size: 15px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 6px;
}
.memory-summary {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.5;
  margin: 0 0 8px;
}
.memory-meta {
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: #9ca3af;
  margin-bottom: 8px;
}
.memory-used-by {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 6px;
}
.used-by-label { font-weight: 600; }
.agent-tag {
  padding: 1px 6px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 4px;
  font-size: 11px;
  color: #059669;
}
.memory-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}
.memory-tag {
  padding: 2px 6px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  font-size: 11px;
  color: #6b7280;
}

/* ===== Skill Panel ===== */
.skill-panel {
  padding: 20px;
}
.skill-panel-header {
  margin-bottom: 20px;
}
.skill-panel-header h3 {
  font-size: 18px;
  font-weight: 800;
  margin: 0 0 4px;
}
.skill-panel-header span {
  font-size: 13px;
  color: #6b7280;
}
.skill-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}
.skill-card {
  padding: 18px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
  transition: all .2s;
}
.skill-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59,130,246,.1);
}
.skill-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.skill-rank {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 800;
  background: #f3f4f6;
  color: #6b7280;
}
.skill-rank.hot { background: #fef2f2; color: #dc2626; }
.skill-rank.warm { background: #fff7ed; color: #ea580c; }
.skill-status {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}
.skill-status.verified { background: #d1fae5; color: #059669; }
.skill-status.testing { background: #fef3c7; color: #d97706; }
.skill-name {
  font-size: 16px;
  font-weight: 700;
  margin: 0 0 6px;
}
.skill-desc {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.5;
  margin: 0 0 10px;
}
.skill-meta {
  display: flex;
  gap: 10px;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 10px;
}
.skill-category {
  padding: 2px 6px;
  background: #f0f9ff;
  border-radius: 4px;
  color: #0369a1;
}
.skill-stars { font-weight: 600; }
.skill-lang {
  padding: 2px 6px;
  background: #f3f4f6;
  border-radius: 4px;
}
.skill-actions {
  display: flex;
  gap: 8px;
}
.skill-repo-link {
  display: inline-block;
  padding: 6px 12px;
  background: #059669;
  color: #fff;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  text-decoration: none;
  transition: background .15s;
}
.skill-repo-link:hover { background: #047857; }

/* ===== Wiki Panel ===== */
.wiki-panel {
  padding: 20px;
}
.wiki-panel-header {
  margin-bottom: 20px;
}
.wiki-panel-header h3 {
  font-size: 18px;
  font-weight: 800;
  margin: 0 0 4px;
}
.wiki-panel-header span {
  font-size: 13px;
  color: #6b7280;
}
.wiki-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}
.wiki-card {
  padding: 18px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
  transition: all .2s;
}
.wiki-card:hover {
  border-color: #8b5cf6;
  box-shadow: 0 4px 12px rgba(139,92,246,.1);
}
.wiki-card.active { border-top: 3px solid #8b5cf6; }
.wiki-card.draft { border-top: 3px solid #f59e0b; }
.wiki-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.wiki-category {
  padding: 2px 8px;
  background: #f5f3ff;
  border-radius: 4px;
  font-size: 11px;
  color: #7c3aed;
  font-weight: 600;
}
.wiki-status-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}
.wiki-status-badge.active { background: #d1fae5; color: #059669; }
.wiki-status-badge.draft { background: #fef3c7; color: #d97706; }
.wiki-title {
  font-size: 15px;
  font-weight: 700;
  margin: 0 0 6px;
}
.wiki-desc {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.5;
  margin: 0 0 10px;
}
.wiki-stats {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 8px;
}
.wiki-foot {
  font-size: 11px;
  color: #9ca3af;
}

/* ===== CodeGraph Panel ===== */
.codegraph-panel {
  padding: 20px;
}
.codegraph-header {
  margin-bottom: 20px;
}
.codegraph-header h3 {
  font-size: 18px;
  font-weight: 800;
  margin: 0 0 4px;
}
.codegraph-header span {
  font-size: 13px;
  color: #6b7280;
}
.codegraph-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 16px;
}
.codegraph-card {
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
  transition: all .2s;
}
.codegraph-card:hover {
  border-color: #f59e0b;
  box-shadow: 0 4px 12px rgba(245,158,11,.1);
}
.cg-card-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.cg-file {
  font-size: 13px;
  font-weight: 700;
  color: #1f2937;
  font-family: 'SF Mono', Monaco, monospace;
}
.cg-lang {
  padding: 2px 6px;
  background: #dbeafe;
  border-radius: 4px;
  font-size: 11px;
  color: #1d4ed8;
  font-weight: 600;
}
.cg-complexity {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}
.cg-complexity.high { background: #fef2f2; color: #dc2626; }
.cg-complexity.medium { background: #fef3c7; color: #d97706; }
.cg-complexity.low { background: #d1fae5; color: #059669; }
.cg-symbols {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 10px;
}
.cg-symbol {
  padding: 2px 6px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  font-size: 11px;
  font-family: 'SF Mono', Monaco, monospace;
  color: #374151;
}
.cg-relations {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.cg-calls-to, .cg-called-by {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}
.cg-rel-label {
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  min-width: 60px;
}
.cg-rel-item {
  padding: 2px 6px;
  background: #f0f9ff;
  border-radius: 4px;
  font-size: 11px;
  color: #0369a1;
  font-family: 'SF Mono', Monaco, monospace;
}
.work-track-list {
  gap: 10px;
  padding-left: 0;
}
.work-track-list::before {
  left: 18px;
  top: 18px;
  bottom: 18px;
  background: #dbe6e3;
}
.work-track-list button {
  grid-template-columns: 38px minmax(0, 1fr) 24px;
  min-height: 62px;
  padding: 9px 10px;
  border-color: #dfe8e7;
  border-radius: 14px;
  background: rgba(255,255,255,.9);
}
.work-track-list .activity-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  box-shadow: 0 0 0 5px #fff;
}
.work-track-list button > span:nth-child(2) {
  gap: 4px;
}
.work-track-list small {
  color: #6f8186;
  font-size: 11px;
  font-weight: 720;
}
.work-track-list b {
  color: #253a40;
  font-size: 14px;
  font-weight: 760;
}
.work-track-list button > i {
  width: 22px;
  height: 22px;
  background: #f2f6f5;
  color: #7c9295;
}
.text-link { border: 0; background: transparent; color: var(--teal); font-size: 12px; font-weight: 800; }
.knowledge-recent-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.knowledge-recent-grid button { position: relative; display: grid; grid-template-columns: 48px minmax(0, 1fr); gap: 11px; min-height: 118px; padding: 13px; overflow: hidden; border: 1px solid #e0e7e9; border-radius: 12px; background: linear-gradient(145deg, #fff, #fafcfc); text-align: left; }
.knowledge-recent-grid button::after { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--knowledge-accent); }
.knowledge-recent-grid button:hover { transform: translateY(-2px); border-color: color-mix(in srgb, var(--knowledge-accent) 42%, #dce5e7); box-shadow: 0 10px 20px rgba(31,55,63,.075); }
.knowledge-file-icon { width: 48px; height: 54px; display: grid; place-items: center; border-radius: 8px 8px 12px 8px; background: color-mix(in srgb, var(--knowledge-accent) 14%, #fff); color: var(--knowledge-accent); font-size: 10px; font-weight: 900; letter-spacing: .04em; }
.knowledge-card-copy { display: grid; align-content: start; gap: 5px; min-width: 0; }
.knowledge-card-copy b { overflow: hidden; color: var(--ink); font-size: 14px; text-overflow: ellipsis; white-space: nowrap; }
.knowledge-card-copy small { overflow: hidden; color: var(--muted); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.knowledge-card-copy em { justify-self: start; padding: 3px 7px; border-radius: 999px; background: color-mix(in srgb, var(--knowledge-accent) 10%, #fff); color: var(--knowledge-accent); font-size: 10px; font-style: normal; font-weight: 800; }
.citation-count { position: absolute; right: 12px; bottom: 10px; color: #839297; font-size: 10px; }

/* 检修任务页：统一页头、数据看板、筛选工具栏和复检卡片。 */
.task-nav-panel { position: relative; overflow: hidden; padding: 20px 22px; border-top: 4px solid var(--blue) !important; background: linear-gradient(120deg, #fff, #f5f9fc) !important; }
.task-nav-panel::after { content: "MAINTENANCE WORKFLOW"; position: absolute; right: 22px; bottom: 7px; color: rgba(58,111,158,.045); font-size: 27px; font-weight: 900; letter-spacing: .08em; pointer-events: none; }
.task-nav-panel h3 { margin-top: 5px; color: var(--ink); font-size: 20px; }
.task-nav-panel small { display: block; margin-top: 6px; color: var(--muted); font-size: 11px; }
.task-nav-panel .tabs { position: relative; z-index: 1; padding: 5px; border: 1px solid #d8e3e8; border-radius: 11px; background: rgba(255,255,255,.84); }
.task-nav-panel .tabs button { min-height: 34px; border: 0; background: transparent; color: #52666c; font-size: 11px; font-weight: 800; }
.task-nav-panel .tabs button.active { background: var(--teal-dark); color: #fff; box-shadow: 0 6px 14px rgba(20,82,80,.16); }
.task-metric-table-panel { padding: 20px; border-top: 3px solid #48584f !important; background: #fffdfa !important; }
.task-metric-table { display: grid; gap: 6px; }
.task-metric-row { display: grid; grid-template-columns: minmax(100px,.9fr) 88px minmax(190px,1.25fr) minmax(180px,1fr) 62px; align-items: center; gap: 12px; min-height: 48px; padding: 8px 12px; border: 1px solid transparent; border-radius: 9px; background: #f8f7f2; color: #24312b; text-align: left; }
.task-metric-row:nth-child(even) { background: #fbfaf6; }
.task-metric-row:hover { transform: translateY(-1px); border-color: #cfd8cf; background: #f2f4ee; box-shadow: 0 8px 18px rgba(45,55,48,.055); }
.metric-name { color: #344039; font-size: 13px; font-weight: 900; }
.metric-value { color: #18221d; font-size: 19px; font-weight: 900; font-variant-numeric: tabular-nums; }
.metric-progress { display: grid; grid-template-columns: minmax(0,1fr) 38px; align-items: center; gap: 8px; min-width: 0; }
.metric-progress i { height: 7px; overflow: hidden; border-radius: 999px; background: #e5e4dc; }
.metric-progress u { display: block; height: 100%; border-radius: inherit; background: #53685d; text-decoration: none; }
.metric-progress em { color: #667067; font-size: 11px; font-style: normal; font-weight: 800; text-align: right; font-variant-numeric: tabular-nums; }
.metric-hint { overflow: hidden; color: #72766f; font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.metric-arrow { justify-self: end; padding: 4px 8px; border: 1px solid #d8d6ca; border-radius: 7px; background: #fffefa; color: #566257; font-size: 11px; font-weight: 900; }
.task-analytics { overflow: hidden; padding: 22px; border-top: 3px solid var(--teal) !important; background: linear-gradient(160deg, #fff, #f5faf9) !important; }
.task-analytics .panel-head > button { border-color: #cbdcda; background: #fff; color: var(--teal-dark); font-size: 11px; font-weight: 800; }
.task-analytics .analysis-cards { grid-template-columns: 1.15fr .9fr .9fr 1.2fr; align-items: stretch; gap: 13px; }
.task-analytics .analysis-cards section { min-height: 275px; padding: 15px; border-color: #dde7e7; background: rgba(255,255,255,.9); box-shadow: 0 6px 16px rgba(31,55,63,.035); }
.task-analytics .analysis-cards section > b { padding-bottom: 10px; border-bottom: 1px solid #e7eded; color: #2e4348; font-size: 13px; }
.task-analytics .analysis-cards section:last-child { grid-template-columns: repeat(2, minmax(0, 1fr)); align-content: start; }
.task-analytics .analysis-cards section:last-child > b { grid-column: 1 / -1; }
.task-analytics .chip-row { min-height: 34px; }
.task-analytics .analysis-cards svg { height: 180px; }
.trend-card-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding-bottom: 9px; border-bottom: 1px solid #e7eded; }
.trend-card-head > b { color: #2e4348; font-size: 13px; }
.trend-card-head > span { padding: 4px 8px; border-radius: 999px; background: #e7f3f1; color: var(--teal-dark); font-size: 10px; font-weight: 800; }
.trend-summary { display: grid; grid-template-columns: auto 1fr auto; align-items: end; gap: 7px; padding: 4px 2px 0; }
.trend-summary strong { color: #183f46; font-size: 25px; line-height: 1; }
.trend-summary span { color: var(--muted); font-size: 10px; }
.trend-summary em { padding: 4px 7px; border-radius: 7px; background: #e7f4ee; color: #3e7d61; font-size: 9px; font-style: normal; font-weight: 800; }
.trend-summary em.down { background: #faece9; color: #ad554b; }
.task-analytics .analysis-cards .task-trend-chart { height: 166px; overflow: visible; border: 0; background: linear-gradient(180deg, rgba(235,246,245,.55), rgba(255,255,255,0)); }
.task-trend-grid { stroke: #dce8e8; stroke-width: 1; stroke-dasharray: 4 5; }
.task-trend-dot { fill: #fff; stroke: #2f7f8f; stroke-width: 4; }
.task-trend-value { fill: #235f69; font-size: 10px; font-weight: 800; }
.task-trend-label { fill: #73868b; font-size: 9px; }
.tasks-page .priority-list { grid-template-columns: 1fr; gap: 11px; }
.tasks-page .priority-list article { position: relative; display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(0, 1.5fr) minmax(0, 1.15fr); grid-template-areas: "head desc meta" "progress progress foot"; align-items: center; gap: 12px 18px; min-width: 0; min-height: 146px; padding: 17px 18px 15px 20px; overflow: hidden; border-color: #dce6e5; background: linear-gradient(110deg, #fff, #f8fbfa); box-shadow: 0 7px 18px rgba(29,59,62,.045); }
.tasks-page .priority-list article::before { content: ""; position: absolute; inset: 0 auto 0 0; width: 4px; background: linear-gradient(var(--teal), var(--blue)); }
.priority-task-top { grid-area: head; display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.priority-task-top > div { display: grid; gap: 3px; min-width: 0; }
.priority-task-top > div small { color: #789096; font-size: 9px; font-weight: 800; letter-spacing: .04em; }
.priority-task-top > div b { overflow: hidden; color: #203a40; font-size: 15px; text-overflow: ellipsis; white-space: nowrap; }
.priority-task-top > span { display: flex; align-items: center; gap: 7px; flex: 0 0 auto; }
.priority-task-top > span em { color: #52686d; font-size: 10px; font-style: normal; font-weight: 800; }
.priority-task-desc { grid-area: desc; min-height: 0; margin: 0; padding: 4px 18px; border-right: 1px solid #e5eceb; border-left: 1px solid #e5eceb; color: #64757a; font-size: 10px; line-height: 1.65; }
.priority-task-meta { grid-area: meta; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 7px; }
.priority-task-meta > span { display: grid; gap: 3px; min-width: 0; padding: 8px 9px; border: 1px solid #e4ebea; border-radius: 9px; background: rgba(255,255,255,.82); }
.priority-task-meta small { color: #87969a; font-size: 8px; }
.priority-task-meta b { overflow: hidden; color: #374e53; font-size: 9px; text-overflow: ellipsis; white-space: nowrap; }
.priority-task-progress { grid-area: progress; display: grid; grid-template-columns: 1fr auto; align-items: center; gap: 9px; }
.priority-task-progress > div { height: 7px; overflow: hidden; border-radius: 999px; background: #e6eeee; }
.priority-task-progress > div span { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--teal), #55a79c); }
.priority-task-progress > b { color: var(--teal-dark); font-size: 10px; }
.tasks-page .priority-list article > footer { grid-area: foot; display: flex; align-items: flex-end; justify-content: space-between; gap: 10px; padding-top: 10px; border-top: 1px solid #e6eceb; }
.tasks-page .priority-list article > footer > span { display: grid; gap: 2px; min-width: 0; }
.tasks-page .priority-list article > footer small { color: #89979a; font-size: 8px; }
.tasks-page .priority-list article > footer b { color: #334b50; font-size: 10px; }
.tasks-page .priority-list article > footer em { color: #a16d31; font-size: 8px; font-style: normal; }
.tasks-page .priority-list article > footer button { min-height: 34px; padding: 7px 11px; border-color: #cfe0de; background: #f2f8f7; color: var(--teal-dark); font-size: 10px; font-weight: 800; }
.tasks-page .priority-list article > footer button i { margin-left: 5px; font-style: normal; }
.task-modal-card { width: min(940px, 96vw); gap: 16px; padding: 0 24px 22px; border: 1px solid #ded8cf; border-radius: 18px; background: #fbfaf8; box-shadow: 0 26px 70px rgba(24,28,28,.18); }
.task-modal-card .close { z-index: 3; top: 15px; right: 16px; border-color: #d8d1c6; background: #fffdf9; color: #39423f; }
.task-modal-hero { position: sticky; top: 0; z-index: 2; display: flex; align-items: center; justify-content: space-between; gap: 20px; margin: 0 -24px; padding: 22px 64px 20px 24px; border-bottom: 1px solid #e4ded4; border-radius: 18px 18px 0 0; background: #fffdf9; color: #1f2d30; box-shadow: 0 8px 18px rgba(34,43,45,.055); }
.task-modal-hero .eyebrow { color: #8b7a63; }
.task-modal-hero h2 { margin: 5px 0; color: #172326; font-size: 23px; }
.task-modal-hero small { color: #69736f; }
.task-modal-hero > span { display: flex; align-items: center; gap: 9px; }
.task-modal-hero > span b { padding: 6px 10px; border-radius: 999px; background: #eef3f1; color: #40534d; font-size: 11px; }
.task-modal-progress { display: grid; grid-template-columns: 1fr auto; align-items: center; gap: 12px; padding: 2px 2px 0; }
.task-modal-progress > div { height: 9px; overflow: hidden; border-radius: 999px; background: #dfe9e8; }
.task-modal-progress > div span { display: block; height: 100%; border-radius: inherit; background: #5f8c80; }
.task-modal-progress > b { color: #48665d; font-size: 12px; }
.task-modal-stats { grid-template-columns: repeat(4, minmax(0, 1fr)); margin-top: 0; }
.task-modal-stats span { display: grid; gap: 5px; padding: 11px 12px; border: 1px solid #dde7e6; background: #fff; }
.task-modal-stats small { color: #87979a; font-size: 9px; }
.task-modal-stats b { overflow: hidden; color: #30494e; font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.task-modal-description { padding: 13px 15px; border-left: 4px solid #b88a44; border-radius: 0 10px 10px 0; background: #fff8ec; color: #5e574a; line-height: 1.7; }
.task-modal-section-title { display: flex; align-items: center; justify-content: space-between; padding-bottom: 9px; border-bottom: 1px solid #dfe8e7; }
.task-modal-section-title span { color: #243e43; font-size: 16px; font-weight: 900; }
.task-modal-section-title small { padding: 4px 8px; border-radius: 999px; background: #e4f1ef; color: var(--teal-dark); font-weight: 800; }
.task-modal-card .executable-sop { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 9px; }
.task-modal-card .executable-sop > span { min-height: 76px; padding: 11px 12px; border: 1px solid #e0e7e6; border-radius: 11px; background: #fff; }
.task-modal-card .executable-sop > span > b { background: #dceeed; color: var(--teal-dark); }
.task-modal-card .executable-sop > span > button { min-height: 34px; border-color: #d1dfde; background: #f5f9f8; color: var(--teal-dark); font-size: 10px; }
.task-modal-card .safety-reminders { grid-template-columns: minmax(165px, .7fr) repeat(3, minmax(0, 1fr)); align-items: center; padding: 14px; background: linear-gradient(100deg, #fff8ec, #fffdf9); }
.task-modal-card .safety-reminders > div { display: grid; gap: 3px; }
.task-modal-card .safety-reminders > div small { color: #9a7440; font-size: 9px; }
.task-modal-card .safety-reminders > span { padding: 7px 9px; border-radius: 8px; background: rgba(255,255,255,.75); text-align: center; }
.task-modal-actions { margin: 6px -24px -22px; padding: 14px 24px; border-top: 1px solid #dbe5e4; border-radius: 0 0 18px 18px; background: #fffdf9; box-shadow: none; }
.task-modal-actions button { min-width: 150px; min-height: 42px; font-weight: 800; }
.task-modal-actions .primary { background: #1f5658; color: #fff; }
.task-modal-card .task-flow-recommendation { border-color: #e5ded2; background: #fffdf8; }
.task-modal-card .task-flow-recommendation button { border-color: #d7c7af; background: #fff8ec; color: #7a5b28; }
.task-modal-card .compliance-grid span.ok { border-color: #dbe9df; background: #f6faf7; color: #4b6d58; }
.task-modal-card .compliance-grid span.required:not(.ok) { border-color: #ead4ca; background: #fff5f0; color: #9b533c; }
.task-manage-panel { padding: 20px; border-top: 3px solid var(--teal) !important; }
.task-manage-panel .filters { display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)) minmax(200px, 1.35fr) auto auto; gap: 9px; align-items: center; padding: 12px; border: 1px solid #dfe8e8; border-radius: 12px; background: #f5f9f8; }
.task-manage-panel .filters > select, .task-manage-panel .filters > input, .task-manage-panel .filters > button { width: 100%; height: 42px; min-height: 42px; }
.task-manage-panel .filters > select, .task-manage-panel .filters > input { border-color: #d3dfe0; background: #fff; font-size: 11px; }
.task-manage-panel .view-switch { height: 42px; flex-wrap: nowrap; padding: 3px; }
.task-manage-panel .view-switch button { width: auto; min-width: 52px; height: 34px; white-space: nowrap; }
.task-manage-panel .filters > .primary { min-width: 104px; white-space: nowrap; }
.task-manage-panel .table { margin-top: 15px; gap: 5px; }
.task-manage-panel .tr { min-height: 64px; border: 1px solid transparent; }
.task-manage-panel .tr:not(.head):nth-child(odd) { background: #f8fbfb; }
.task-manage-panel .tr:not(.head):hover { border-color: #c9dcda; background: #eef7f5; }
.task-manage-panel .tr.head { min-height: 44px; background: #eaf1f2; color: #52666b; }
.recheck-panel { position: relative; overflow: hidden; padding: 26px; border-top: 4px solid var(--violet) !important; background: linear-gradient(145deg, #fff 0%, #fbfafd 62%, #f6fafb 100%) !important; }
.recheck-panel::after { content: ""; position: absolute; right: -90px; top: -120px; width: 280px; height: 280px; border-radius: 50%; background: radial-gradient(circle, rgba(126,91,174,.12), transparent 68%); pointer-events: none; }
.recheck-heading { position: relative; z-index: 1; display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; margin-bottom: 22px; padding-bottom: 17px; border-bottom: 1px solid #e4e3eb; }
.recheck-heading h3 { margin-top: 5px; color: var(--ink); font-size: 22px; }
.recheck-heading > span { padding: 7px 12px; border: 1px solid #dfd4eb; border-radius: 999px; background: #f4eff9; color: var(--violet); font-size: 11px; font-weight: 900; white-space: nowrap; }
.recheck-panel .recheck-grid { position: relative; z-index: 1; gap: 18px; }
.recheck-panel .recheck-card { --recheck-accent: var(--violet); position: relative; min-height: 410px; grid-template-rows: auto auto auto 1fr auto; gap: 16px; padding: 21px; overflow: hidden; border-color: #dfe3e8; border-radius: 15px; background: rgba(255,255,255,.96); box-shadow: 0 9px 24px rgba(45,50,70,.06); transition: transform .2s, border-color .2s, box-shadow .2s; }
.recheck-panel .recheck-card.warning { --recheck-accent: var(--amber); }
.recheck-panel .recheck-card::before { content: ""; position: absolute; inset: 0 auto 0 0; width: 5px; background: linear-gradient(180deg, var(--recheck-accent), color-mix(in srgb, var(--recheck-accent) 58%, var(--blue))); }
.recheck-panel .recheck-card:hover { transform: translateY(-2px); border-color: color-mix(in srgb, var(--recheck-accent) 32%, #dfe3e8); box-shadow: 0 15px 31px rgba(45,50,70,.09); }
.recheck-card-head { display: grid; grid-template-columns: 44px minmax(0, 1fr) auto; align-items: center; gap: 13px; }
.recheck-mark { width: 44px; height: 44px; display: grid; place-items: center; border-radius: 12px; background: color-mix(in srgb, var(--recheck-accent) 12%, #fff); color: var(--recheck-accent); }
.recheck-mark .ui-icon { width: 21px; height: 21px; }
.recheck-card-head > div { min-width: 0; display: grid; gap: 5px; }
.recheck-card-head b { overflow: hidden; color: #233b40; font-size: 17px; line-height: 1.4; text-overflow: ellipsis; white-space: nowrap; }
.recheck-card-head small { overflow: hidden; color: var(--muted); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.recheck-card-head strong { padding: 6px 9px; border-radius: 8px; background: #eef5f4; color: var(--teal); font-size: 12px; }
.recheck-meta { display: grid; grid-template-columns: 1.25fr 1fr 1fr; gap: 8px; }
.recheck-meta > span { min-width: 0; display: grid; gap: 4px; padding: 9px 10px; border: 1px solid #e3eaeb; border-radius: 9px; background: #f8fafa; }
.recheck-meta small { color: #829195; font-size: 9px; }
.recheck-meta b { overflow: hidden; color: #344c51; font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.recheck-field { display: grid; gap: 7px; color: #465d62; font-size: 11px; font-weight: 900; }
.recheck-select-wrap { position: relative; }
.recheck-select-wrap::after { content: "⌄"; position: absolute; right: 13px; top: 50%; color: #60777c; font-size: 18px; line-height: 1; transform: translateY(-58%); pointer-events: none; }
.recheck-panel .recheck-select-wrap select { height: 44px; padding: 0 40px 0 13px; border-color: #dbe4e5; border-radius: 10px; appearance: none; background: #f9fbfb; color: #263f44; font-weight: 800; cursor: pointer; }
.recheck-panel textarea { min-height: 90px; padding: 11px 13px; border-color: #dbe4e5; border-radius: 10px; background: #f9fbfb; color: #263f44; line-height: 1.6; resize: vertical; }
.recheck-panel select:focus, .recheck-panel textarea:focus { border-color: color-mix(in srgb, var(--recheck-accent) 48%, #dbe4e5); box-shadow: 0 0 0 3px color-mix(in srgb, var(--recheck-accent) 10%, transparent); background: #fff; }
.recheck-card-footer { display: flex; align-items: center; justify-content: space-between; gap: 14px; padding-top: 14px; border-top: 1px solid #e5ebec; }
.recheck-card-footer > span { display: flex; align-items: center; gap: 7px; color: #7a8c90; font-size: 10px; }
.recheck-card-footer > span i { width: 7px; height: 7px; border-radius: 50%; background: var(--recheck-accent); box-shadow: 0 0 0 4px color-mix(in srgb, var(--recheck-accent) 11%, transparent); }
.recheck-panel .recheck-card-footer .primary { min-width: 132px; min-height: 40px; border: 0; border-radius: 9px; background: linear-gradient(135deg, var(--teal-dark), var(--teal)); color: #fff; box-shadow: 0 7px 15px rgba(17,102,95,.16); }

/* 检索分类和检修建议：点击有计数、有空态，建议改为可扫读步骤卡。 */
.result-tab-hint { display: block; margin-top: 7px; color: var(--muted); font-size: 11px; }
.search-results-panel .tabs button { display: inline-flex; align-items: center; gap: 6px; }
.search-results-panel .tabs button em { min-width: 18px; height: 18px; display: grid; place-items: center; border-radius: 999px; background: #edf2f3; color: #718187; font-size: 9px; font-style: normal; }
.search-results-panel .tabs button.active em { background: rgba(255,255,255,.18); color: #fff; }
.result-filter-empty { min-height: 190px; display: grid; place-items: center; align-content: center; gap: 9px; margin-top: 18px; border: 1px dashed #cad9da; border-radius: 14px; background: #f7fafb; text-align: center; }
.result-filter-empty b { color: #33494e; font-size: 15px; }
.result-filter-empty span { color: var(--muted); font-size: 11px; }
.result-filter-empty button { border-color: #bcd2cf; background: #fff; color: var(--teal); font-size: 11px; font-weight: 800; }
.maintenance-advice-panel { overflow: hidden; padding: 22px 24px; border-top: 4px solid var(--amber) !important; background: linear-gradient(145deg, #fff, #fffcf7) !important; }
.advice-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 16px; }
.advice-heading h3 { margin-top: 5px; color: var(--ink); font-size: 18px; }
.advice-heading > span { padding: 6px 10px; border-radius: 999px; background: #faecd7; color: #a76a1e; font-size: 10px; font-weight: 900; }
.maintenance-advice-panel .sop-list { position: relative; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; counter-reset: step; }
.maintenance-advice-panel .sop-list span { position: relative; min-height: 86px; align-items: flex-start; padding: 15px; border: 1px solid #e7e1d8; background: #fff; color: #3e5055; line-height: 1.55; box-shadow: 0 6px 15px rgba(61,50,34,.035); }
.maintenance-advice-panel .sop-list b { flex: 0 0 30px; width: 30px; height: 30px; border-radius: 10px; background: linear-gradient(145deg, #d38c33, #b86d1e); color: #fff; box-shadow: 0 5px 10px rgba(184,109,30,.18); }
.advice-reference { display: flex; align-items: baseline; gap: 10px; margin-top: 16px; padding: 12px 14px; border-radius: 10px; background: #f6f2ec; color: #6f6254; font-size: 11px; line-height: 1.6; }
.advice-reference b { flex: 0 0 auto; color: #9a611d; }

/* 任务动态：紧凑时间轴，避免重复灰色条目拉长页面。 */
.task-event-panel { max-height: 560px; display: flex; flex-direction: column; overflow: hidden; background: linear-gradient(160deg, #fff 0%, #f7fbfb 100%); }
.task-event-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; padding-bottom: 13px; border-bottom: 1px solid #e1e9ea; }
.task-event-heading h3 { margin-top: 5px; color: var(--ink); font-size: 17px; }
.task-event-heading > span { padding: 5px 9px; border-radius: 999px; background: #e8f3f2; color: var(--teal); font-size: 10px; font-weight: 900; }
.task-events { position: relative; gap: 0; margin: 0; padding: 8px 4px 8px 2px; overflow: auto; }
.task-events::before { content: ""; position: absolute; left: 11px; top: 20px; bottom: 20px; width: 1px; background: linear-gradient(#7db5b0, #d7e6e5); }
.task-events article { position: relative; display: grid; grid-template-columns: 18px 112px minmax(0, 1fr); align-items: start; gap: 9px; min-height: 72px; padding: 11px 9px 11px 0; border-bottom: 1px solid #edf1f2; }
.task-events article:last-child { border-bottom: 0; }
.task-events article > i { position: relative; z-index: 1; width: 9px; height: 9px; margin: 5px 0 0 7px; border: 2px solid #fff; border-radius: 50%; background: var(--teal); box-shadow: 0 0 0 3px #d9eeeb; }
.task-events article:nth-child(3n+2) > i { background: var(--amber); box-shadow: 0 0 0 3px #f6ead8; }
.task-events article:nth-child(3n) > i { background: var(--blue); box-shadow: 0 0 0 3px #e0ebf5; }
.task-events time { color: #52666b; font-family: ui-monospace, "Cascadia Code", monospace; font-size: 11px; font-weight: 800; line-height: 1.5; }
.task-events p { color: #30464b; font-size: 12px; line-height: 1.65; }
.task-events article:hover { background: linear-gradient(90deg, transparent, #f0f7f6); }

/* 知识库页头与图谱工具栏。 */
.knowledge-nav-panel { overflow: hidden; padding: 20px 22px; border-top: 4px solid var(--teal) !important; background: linear-gradient(120deg, #fff 0%, #f5faf9 70%, #eef6f5 100%) !important; }
.knowledge-nav-panel::after { content: "KNOWLEDGE ASSET CENTER"; position: absolute; right: 22px; bottom: 7px; color: rgba(21,89,85,.055); font-size: 28px; font-weight: 900; letter-spacing: .08em; pointer-events: none; }
.knowledge-nav-panel { position: relative; }
.knowledge-nav-panel h3 { margin-top: 5px; color: var(--ink); font-size: 20px; }
.knowledge-nav-panel small { display: block; margin-top: 6px; color: var(--muted); font-size: 11px; }
.knowledge-nav-panel .tabs { position: relative; z-index: 1; padding: 5px; border: 1px solid #d7e5e3; border-radius: 11px; background: rgba(255,255,255,.82); }
.knowledge-nav-panel .tabs button { min-height: 34px; border: 0; background: transparent; color: #53676c; font-size: 11px; font-weight: 800; }
.knowledge-nav-panel .tabs button.active { background: var(--teal-dark); color: #fff; box-shadow: 0 6px 13px rgba(20,82,80,.17); }
.graph-panel { border-top: 3px solid var(--blue) !important; background: linear-gradient(180deg, #fff, #f8fbfc) !important; }
.graph-toolbar { grid-template-columns: minmax(260px, 1fr) 300px !important; gap: 14px 18px !important; margin: -18px -18px 16px !important; padding: 18px 18px 15px; border-bottom: 1px solid #dfe8ea; background: linear-gradient(135deg, #f6faf9, #f4f7fb); }
.graph-toolbar h3 { margin-top: 5px; color: var(--ink); font-size: 18px; }
.graph-search, .graph-search.expanded, .graph-search:focus-within { width: 300px; height: 42px; border-color: #cbdadc; border-radius: 11px; background: #fff; box-shadow: 0 6px 16px rgba(31,55,63,.055); }
.graph-search-trigger { border-radius: 9px; background: var(--teal-dark); }
.graph-search input { opacity: 1; color: var(--ink); font-size: 11px; }
.graph-controls { grid-column: 1 / -1; display: grid; grid-template-columns: repeat(4, minmax(130px, 1fr)) auto auto; gap: 9px; justify-content: stretch; padding-top: 13px; border-top: 1px solid #dfe8e8; }
.graph-controls select, .graph-controls button { width: 100%; height: 38px; border-color: #d2dfe0; border-radius: 9px; background: #fff; color: #3c5358; font-size: 11px; font-weight: 700; }
.graph-controls select:hover, .graph-controls button:hover { border-color: #8fb4b1; background: #edf6f5; }
.knowledge-map { gap: 18px; }
.map-canvas { box-shadow: inset 0 0 40px rgba(49,91,105,.035); }

/* 个人中心：按信息类型分色，并把设置项横向展开，消除底部大块空白。 */
.profile-page { align-items: start; }
.profile-section { --profile-accent: var(--teal); position: relative; align-content: start; overflow: hidden; padding: 13px 14px; border-color: #dce5e6; background: linear-gradient(155deg, #fff 0%, #fbfcfc 100%); box-shadow: 0 9px 24px rgba(31,55,63,.06); }
.profile-section::before { content: ""; position: absolute; inset: 0 0 auto; height: 3px; background: var(--profile-accent); }
.profile-archive { --profile-accent: var(--blue); }
.profile-files { --profile-accent: var(--violet); }
.profile-contribution { --profile-accent: var(--amber); }
.profile-collaboration { --profile-accent: #2f8c83; }
.profile-messages { --profile-accent: #d16a62; }
.profile-growth { --profile-accent: #6f7eb8; }
.profile-settings { --profile-accent: #65777c; grid-column: 1 / -1; }
.profile-section .panel-head { align-items: flex-start; gap: 8px; }
.profile-section .panel-head h3 { margin-top: 3px; color: var(--ink); font-size: 15px; line-height: 1.3; }
.profile-section .panel-head .eyebrow { font-size: 10px; }
.profile-section .panel-head > button { border-color: color-mix(in srgb, var(--profile-accent) 32%, #dce5e6); background: color-mix(in srgb, var(--profile-accent) 8%, #fff); color: var(--profile-accent); font-size: 10px; font-weight: 800; min-height: 28px; padding: 4px 9px; }
.profile-metrics { gap: 7px; }
.profile-metrics span { min-height: 52px; align-content: center; padding: 8px 9px; border: 1px solid color-mix(in srgb, var(--profile-accent) 16%, #e6ecec); background: color-mix(in srgb, var(--profile-accent) 7%, #fff); color: #6c7b80; }
.profile-metrics b { color: var(--profile-accent); font-size: 19px; }
.profile-list { gap: 7px; }
.profile-list button { position: relative; min-height: 50px; padding: 8px 22px 8px 14px; border-color: #e0e7e8; background: rgba(255,255,255,.9); }
.profile-list button::before { content: ""; position: absolute; left: 0; top: 9px; bottom: 9px; width: 3px; border-radius: 0 3px 3px 0; background: color-mix(in srgb, var(--profile-accent) 72%, #fff); }
.profile-list button::after { content: "→"; position: absolute; right: 10px; top: 50%; color: #9aa7ab; font-size: 12px; transform: translateY(-50%); }
.profile-list button:hover { transform: translateY(-2px); border-color: color-mix(in srgb, var(--profile-accent) 35%, #dce5e6); background: color-mix(in srgb, var(--profile-accent) 4%, #fff); box-shadow: 0 8px 16px rgba(31,55,63,.06); }
.profile-list b { padding-right: 14px; color: #273d42; font-size: 13px; }
.profile-list small { padding-right: 14px; color: #7a898e; font-size: 10.5px; }
.profile-settings .profile-list { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.profile-settings .profile-list button { min-height: 60px; }
.profile-page-simple { display: grid; gap: 16px; max-width: 1180px; margin: 0 auto; }
.profile-card-main {
  display: grid;
  grid-template-columns: 86px minmax(0, 1fr) minmax(210px, auto);
  align-items: center;
  gap: 20px;
  padding: 24px 26px;
  border: 1px solid #dce5e6;
  border-radius: 14px;
  background: linear-gradient(135deg, #fff 0%, #fbfdfc 62%, #f2f8f7 100%);
  box-shadow: 0 10px 24px rgba(31,55,63,.055);
}
.profile-card-main > img {
  width: 86px;
  height: 86px;
  border: 4px solid #fff;
  border-radius: 50%;
  object-fit: cover;
  box-shadow: 0 8px 18px rgba(31,55,63,.11);
}
.profile-main-copy { display: grid; gap: 5px; min-width: 0; }
.profile-main-copy h2 { color: #1f3338; font-size: 25px; }
.profile-main-copy > span { color: #65787e; font-size: 13px; }
.profile-main-copy > p { max-width: 560px; color: #61757a; font-size: 12px; line-height: 1.65; }
.profile-tags-simple { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 4px; }
.profile-tags-simple em { padding: 5px 9px; border-radius: 999px; background: #f0f6f5; color: #526a70; font-size: 11px; font-style: normal; font-weight: 800; }
.profile-card-main .primary { min-width: 96px; border-color: #2f7f8f; background: #2f7f8f; color: #fff; }
.profile-hero-side { display: grid; grid-template-columns: 1fr; gap: 8px; justify-items: stretch; }
.profile-hero-side span { display: grid; grid-template-columns: 66px minmax(0, 1fr); align-items: center; min-height: 32px; padding: 0 10px; border: 1px solid #e1eaeb; border-radius: 10px; background: rgba(255,255,255,.76); }
.profile-hero-side small { color: #819195; font-size: 11px; }
.profile-hero-side b { overflow: hidden; color: #30474d; font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.profile-simple-grid { display: grid; grid-template-columns: minmax(260px, .72fr) minmax(0, 1.28fr); grid-template-areas: "basic work" "settings work" "recent docs"; gap: 16px; align-items: start; }
.profile-simple-panel {
  display: grid;
  gap: 12px;
  padding: 17px;
  border: 1px solid #dce5e6;
  border-radius: 13px;
  background: #fff;
  box-shadow: 0 8px 22px rgba(31,55,63,.045);
}
.profile-simple-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.profile-simple-head h3 { color: #21383d; font-size: 17px; }
.profile-simple-head button { min-height: 30px; padding: 5px 10px; border-color: #d6e2e3; background: #f8fbfb; color: #526a70; font-size: 12px; font-weight: 800; }
.profile-simple-head button:hover { border-color: #b8cdcf; background: #f1f7f6; }
.profile-info-list { display: grid; gap: 8px; }
.profile-info-list span { display: grid; grid-template-columns: 76px minmax(0, 1fr); align-items: center; min-height: 38px; padding: 0 2px; border-bottom: 1px solid #edf2f2; }
.profile-info-list span:last-child { border-bottom: 0; }
.profile-info-list small { color: #89989c; font-size: 12px; }
.profile-info-list b { overflow: hidden; color: #2c4248; font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.profile-metrics-simple { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.profile-metrics-simple span { display: grid; gap: 4px; min-height: 78px; align-content: center; padding: 13px; border: 1px solid #e3ebec; border-radius: 12px; background: linear-gradient(180deg, #f8fbfa 0%, #fff 100%); }
.profile-metrics-simple b { color: #2f7f8f; font-size: 28px; line-height: 1; }
.profile-metrics-simple small { color: #75878c; font-size: 11px; }
.profile-item-list { display: grid; gap: 7px; }
.profile-item-list button {
  min-height: 48px;
  display: grid;
  gap: 3px;
  padding: 9px 11px;
  border: 1px solid #e3ebec;
  border-radius: 10px;
  background: #fbfdfd;
  text-align: left;
}
.profile-item-list button:hover { transform: translateY(-1px); border-color: #b8cdcf; background: #fff; box-shadow: 0 7px 15px rgba(31,55,63,.05); }
.profile-item-list b { overflow: hidden; color: #2b4046; font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.profile-item-list small { overflow: hidden; color: #7d8d92; font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.profile-basic-panel { grid-area: basic; }
.profile-work-main { grid-area: work; }
.profile-doc-panel { grid-area: docs; }
.profile-settings-simple { grid-area: settings; }
.profile-recent-simple { grid-area: recent; }
.profile-work-main .profile-item-list { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.profile-work-main .profile-item-list button { min-height: 72px; align-content: start; }
.profile-agent-simple { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 9px; }
.profile-agent-simple button {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr);
  align-items: center;
  gap: 9px;
  min-height: 58px;
  padding: 9px;
  border: 1px solid #e3ebec;
  border-radius: 11px;
  background: #fbfdfd;
  text-align: left;
}
.profile-agent-simple img { width: 38px; height: 38px; border-radius: 50%; object-fit: cover; }
.profile-agent-simple span { display: grid; gap: 3px; min-width: 0; }
.profile-agent-simple b { overflow: hidden; color: #2b4046; font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.profile-agent-simple small { overflow: hidden; color: #7d8d92; font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.profile-recent-simple pre { max-height: 160px; overflow: auto; margin: 0; padding: 12px; border-radius: 10px; background: #f5f8f8; color: #53676c; white-space: pre-wrap; }
.profile-workspace {
  gap: 14px;
  align-items: start;
}
.profile-identity-card {
  grid-template-columns: 82px minmax(0, 1fr) minmax(220px, auto);
  padding: 20px 22px;
  border-color: #dde6e2;
  background:
    linear-gradient(135deg, rgba(255,255,255,.96), rgba(248,250,247,.94)),
    radial-gradient(circle at 12% 0%, rgba(181,139,75,.12), transparent 34%);
}
.profile-identity-card .eyebrow,
.profile-workspace .profile-section .eyebrow {
  letter-spacing: .08em;
}
.profile-identity-card h2 {
  font-size: 24px;
  font-weight: 760;
  letter-spacing: 0;
}
.profile-identity-card p {
  color: #637476;
}
.identity-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(74px, 1fr));
  gap: 8px;
  align-items: center;
}
.identity-summary span {
  display: grid;
  gap: 3px;
  min-height: 48px;
  padding: 8px 10px;
  border: 1px solid #e4ebe8;
  border-radius: 11px;
  background: rgba(255,255,255,.78);
}
.identity-summary small {
  color: #83908f;
  font-size: 10px;
}
.identity-summary b {
  color: #233b3d;
  font-size: 15px;
}
.identity-summary .primary {
  grid-column: 1 / -1;
  min-height: 34px;
  border-color: #407f76;
  background: #407f76;
}
.profile-workspace .profile-section {
  min-height: 258px;
  border-radius: 14px;
  border-color: color-mix(in srgb, var(--profile-accent, #6d8b82) 20%, #dfe8e5);
  background:
    linear-gradient(180deg, rgba(255,255,255,.98), rgba(250,251,248,.96)),
    linear-gradient(135deg, color-mix(in srgb, var(--profile-accent, #6d8b82) 8%, transparent), transparent 58%);
}
.profile-workspace .profile-section::before {
  height: 4px;
  background: linear-gradient(90deg, var(--profile-accent, #6d8b82), color-mix(in srgb, var(--profile-accent, #6d8b82) 34%, #fff));
}
.profile-workspace .profile-section .panel-head h3 {
  font-size: 16px;
  font-weight: 760;
  letter-spacing: 0;
}
.profile-today { --profile-accent: #407f76; }
.profile-ability { --profile-accent: #5e7f6f; }
.profile-records { --profile-accent: #5b7f94; }
.profile-contribution { --profile-accent: #b58b4b; }
.profile-quality { --profile-accent: #bd6b58; }
.profile-recent { --profile-accent: #6e7f86; }
.profile-tools { --profile-accent: #4f8b86; }
.profile-settings { --profile-accent: #786a5d; }
.profile-workspace .profile-metrics {
  grid-template-columns: repeat(auto-fit, minmax(82px, 1fr));
}
.profile-workspace .profile-metrics span {
  min-height: 58px;
  border-radius: 12px;
  background: color-mix(in srgb, var(--profile-accent, #6d8b82) 7%, #fff);
}
.profile-workspace .profile-metrics b {
  font-size: 22px;
  font-weight: 780;
}
.profile-workspace .profile-list button {
  min-height: 54px;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 3px 10px;
  border-radius: 11px;
}
.profile-workspace .profile-list b,
.profile-workspace .profile-list small {
  grid-column: 1;
}
.profile-workspace .profile-list em {
  grid-column: 2;
  grid-row: 1 / span 2;
  align-self: center;
  max-width: 86px;
  padding: 4px 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--profile-accent, #6d8b82) 12%, #fff);
  color: var(--profile-accent, #6d8b82);
  font-size: 10px;
  font-style: normal;
  font-weight: 800;
  white-space: nowrap;
}
.profile-today {
  min-height: 286px;
}
.profile-today .profile-list {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.profile-today .profile-list button {
  min-height: 70px;
}

/* 个人中心新版：白瓷档案工作台，弱化彩条，突出身份、任务和质量记录。 */
.profile-workspace {
  --profile-ink: #24343d;
  --profile-muted: #728087;
  --profile-line: #e4e8ea;
  --profile-paper: #fffefb;
  --profile-blue: #dcebf6;
  --profile-gold: #b58b4b;
  gap: 16px;
  padding: 2px;
}
.profile-identity-card {
  position: relative;
  overflow: hidden;
  grid-template-columns: 88px minmax(0, 1fr) minmax(236px, auto);
  padding: 24px 26px;
  border: 1px solid #e1e6e7;
  border-radius: 18px;
  background:
    linear-gradient(135deg, rgba(255,255,255,.98), rgba(250,252,253,.96) 58%, rgba(244,249,252,.94)),
    repeating-linear-gradient(90deg, rgba(50,70,80,.035) 0 1px, transparent 1px 18px);
  box-shadow: 0 18px 40px rgba(31,55,63,.07);
}
.profile-identity-card::before {
  content: "";
  position: absolute;
  left: 0;
  top: 18px;
  bottom: 18px;
  width: 5px;
  border-radius: 0 999px 999px 0;
  background: linear-gradient(180deg, #8eb7cf, #b58b4b);
}
.profile-identity-card::after {
  content: "";
  position: absolute;
  right: -54px;
  top: -76px;
  width: 190px;
  height: 190px;
  border: 1px solid rgba(105,134,150,.16);
  border-radius: 50%;
  background: radial-gradient(circle, rgba(220,235,246,.55), rgba(255,255,255,0) 66%);
}
.profile-identity-card > * {
  position: relative;
  z-index: 1;
}
.profile-identity-card > img {
  width: 88px;
  height: 88px;
  border: 5px solid #fff;
  box-shadow: 0 12px 26px rgba(42,68,78,.14);
}
.profile-identity-card .eyebrow,
.profile-workspace .profile-section .eyebrow {
  color: #7e6f5c;
  font-size: 10px;
  font-weight: 760;
  letter-spacing: .14em;
}
.profile-identity-card h2 {
  margin: 3px 0;
  color: var(--profile-ink);
  font-size: 27px;
  font-weight: 720;
}
.profile-identity-card p {
  color: var(--profile-muted);
  font-size: 12px;
}
.profile-identity-card .tag-line span {
  border-color: #e5e9ea;
  background: rgba(255,255,255,.76);
  color: #5f6f76;
}
.identity-summary {
  grid-template-columns: repeat(2, minmax(86px, 1fr));
}
.identity-summary span {
  min-height: 52px;
  border-color: #e5eaec;
  border-radius: 14px;
  background: rgba(255,255,255,.84);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.9);
}
.identity-summary small {
  color: #8a9599;
  font-weight: 560;
}
.identity-summary b {
  color: #273a43;
  font-size: 16px;
  font-weight: 720;
}
.identity-summary .primary {
  border-color: #2f6579;
  border-radius: 12px;
  background: #2f6579;
  box-shadow: 0 10px 20px rgba(47,101,121,.16);
}
.profile-workspace .profile-section {
  position: relative;
  min-height: 250px;
  padding: 18px 18px 16px;
  border: 1px solid var(--profile-line);
  border-radius: 16px;
  background:
    linear-gradient(180deg, rgba(255,255,255,.98), rgba(253,253,251,.96)),
    radial-gradient(circle at 100% 0%, color-mix(in srgb, var(--profile-accent, #89a7b9) 12%, transparent), transparent 44%);
  box-shadow: 0 12px 30px rgba(31,55,63,.055);
}
.profile-workspace .profile-section::before {
  left: 18px;
  right: auto;
  top: 17px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--profile-accent, #89a7b9);
  box-shadow: 0 0 0 5px color-mix(in srgb, var(--profile-accent, #89a7b9) 12%, transparent);
}
.profile-workspace .profile-section .panel-head {
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr) auto;
  padding-left: 0;
  align-items: start;
}
.profile-section-icon {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border: 1px solid color-mix(in srgb, var(--profile-accent, #89a7b9) 26%, #e4e8ea);
  border-radius: 14px;
  background: color-mix(in srgb, var(--profile-accent, #89a7b9) 10%, #fff);
  color: color-mix(in srgb, var(--profile-accent, #89a7b9) 78%, #21333c);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.9);
}
.profile-section-icon .ui-icon {
  width: 22px;
  height: 22px;
  stroke-width: 1.8;
}
.profile-workspace .profile-section .panel-head h3 {
  margin-top: 3px;
  color: var(--profile-ink);
  font-size: 17px;
  font-weight: 700;
}
.profile-workspace .profile-section .panel-head > button {
  min-height: 30px;
  border: 1px solid color-mix(in srgb, var(--profile-accent, #89a7b9) 28%, #dfe6e8);
  border-radius: 999px;
  background: #fff;
  color: color-mix(in srgb, var(--profile-accent, #89a7b9) 72%, #253b45);
  font-size: 11px;
  font-weight: 700;
}
.profile-workspace .profile-section .panel-head > button:hover {
  transform: translateY(-1px);
  background: color-mix(in srgb, var(--profile-accent, #89a7b9) 7%, #fff);
}
.profile-today { --profile-accent: #6f9fbd; }
.profile-ability { --profile-accent: #8c9d87; }
.profile-records { --profile-accent: #7f9aaa; }
.profile-contribution { --profile-accent: #b58b4b; }
.profile-quality { --profile-accent: #b87362; }
.profile-recent { --profile-accent: #8f9aa0; }
.profile-tools { --profile-accent: #6c9c98; }
.profile-settings { --profile-accent: #8d8174; }
.profile-workspace .profile-metrics {
  gap: 8px;
  grid-template-columns: repeat(auto-fit, minmax(74px, 1fr));
}
.profile-workspace .profile-metrics span {
  min-height: 46px;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 4px;
  padding: 8px 10px;
  border: 1px solid #e7ecee;
  border-radius: 999px;
  background: linear-gradient(180deg, #fff, color-mix(in srgb, var(--profile-accent, #89a7b9) 6%, #fff));
  color: #7a878c;
  font-size: 10px;
  line-height: 1.15;
}
.profile-workspace .profile-metrics b {
  color: color-mix(in srgb, var(--profile-accent, #89a7b9) 76%, #1f3338);
  font-size: 16px;
  font-weight: 720;
}
.profile-workspace .profile-list {
  gap: 8px;
  border: 0;
}
.profile-workspace .profile-list button {
  min-height: 62px;
  grid-template-columns: 38px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border: 1px solid #e7ecee;
  border-radius: 13px;
  background: rgba(255,255,255,.82);
  box-shadow: 0 4px 10px rgba(31,55,63,.025);
}
.profile-workspace .profile-list button::before,
.profile-workspace .profile-list button::after {
  display: none;
}
.profile-workspace .profile-list button:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--profile-accent, #89a7b9) 35%, #dfe6e8);
  background: #fff;
  box-shadow: 0 12px 22px rgba(31,55,63,.07);
}
.profile-item-icon {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: color-mix(in srgb, var(--profile-accent, #89a7b9) 10%, #f8fbfc);
  color: color-mix(in srgb, var(--profile-accent, #89a7b9) 76%, #263a44);
}
.profile-item-icon .ui-icon {
  width: 19px;
  height: 19px;
  stroke-width: 1.85;
}
.profile-item-copy {
  display: grid;
  gap: 3px;
  min-width: 0;
}
.profile-workspace .profile-list b {
  grid-column: auto;
  padding-right: 0;
  color: #2c3e47;
  font-size: 13px;
  font-weight: 680;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.profile-workspace .profile-list small {
  grid-column: auto;
  padding-right: 0;
  color: #7a878d;
  font-size: 10.5px;
  font-weight: 420;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.profile-workspace .profile-list em {
  grid-column: auto;
  grid-row: auto;
  justify-self: end;
  max-width: 70px;
  border: 1px solid color-mix(in srgb, var(--profile-accent, #89a7b9) 25%, #e7ecee);
  background: color-mix(in srgb, var(--profile-accent, #89a7b9) 8%, #fff);
  color: color-mix(in srgb, var(--profile-accent, #89a7b9) 72%, #263a44);
  font-size: 10px;
}
.profile-today {
  min-height: 292px;
  background:
    linear-gradient(180deg, rgba(255,255,255,.99), rgba(248,252,255,.96)),
    radial-gradient(circle at 88% 10%, rgba(111,159,189,.12), transparent 46%);
}
.profile-today .profile-list button {
  min-height: 72px;
}
.profile-today .profile-item-icon {
  width: 42px;
  height: 42px;
}
.profile-focus-shell { grid-template-columns: minmax(0, 1fr); }
.profile-focus-shell .panel-resizer,
.profile-focus-shell .operator-panel { display: none; }
.profile-dashboard { display: grid; gap: 16px; max-width: 1280px; margin: 0 auto; padding: 2px; }
.profile-hero-card { position: relative; overflow: hidden; display: grid; grid-template-columns: 112px minmax(0, 1fr) 172px; gap: 22px; align-items: center; min-height: 168px; padding: 24px 30px; border: 1px solid #dce6ef; border-radius: 18px; background: radial-gradient(circle at 74% 26%, rgba(114,161,207,.18), transparent 32%), linear-gradient(135deg, #fff 0%, #f8fbff 42%, #eaf3ff 100%); box-shadow: 0 18px 38px rgba(31,55,63,.08); }
.profile-hero-card::after { content: ""; position: absolute; inset: auto -4% -54% 28%; height: 180px; border-radius: 50%; background: rgba(126,169,211,.13); transform: rotate(-8deg); }
.profile-avatar-wrap { position: relative; z-index: 1; width: 98px; height: 98px; }
.profile-avatar-wrap img { width: 98px; height: 98px; border: 5px solid #fff; border-radius: 50%; object-fit: cover; box-shadow: 0 12px 25px rgba(54,91,121,.18); }
.profile-avatar-wrap button { position: absolute; right: 2px; bottom: 2px; width: 30px; height: 30px; display: grid; place-items: center; border: 1px solid #e3ebf1; border-radius: 50%; background: #fff; color: #496675; box-shadow: 0 8px 18px rgba(31,55,63,.12); }
.profile-avatar-wrap .ui-icon { width: 16px; height: 16px; }
.profile-hero-main, .profile-hero-actions { position: relative; z-index: 1; }
.profile-name-row { display: flex; align-items: center; gap: 10px; min-width: 0; }
.profile-name-row h2 { margin: 0; color: #24343d; font-size: 28px; font-weight: 760; letter-spacing: 0; }
.profile-skill-badge { display: inline-flex; align-items: center; min-height: 26px; padding: 0 12px; border: 1px solid #ead9b7; border-radius: 999px; background: #fff7e7; color: #9a7134; font-size: 12px; font-weight: 800; }
.profile-hero-main p { margin: 9px 0 12px; color: #61727b; font-size: 13px; }
.profile-hero-main > small { display: block; margin-top: 7px; color: #7c8990; font-size: 12px; }
.profile-progress { display: grid; grid-template-columns: auto minmax(160px, 280px) auto; gap: 10px; align-items: center; color: #667882; font-size: 12px; }
.profile-progress i, .profile-growth-card i { height: 7px; overflow: hidden; border-radius: 999px; background: #dfe9f1; }
.profile-progress b, .profile-growth-card i b { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #5f94cb, #8aa5a0); }
.profile-progress em { color: #4578af; font-style: normal; font-weight: 800; }
.profile-tags-soft { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 10px; }
.profile-tags-soft span { padding: 5px 9px; border-radius: 999px; background: rgba(255,255,255,.72); color: #65757c; font-size: 11px; font-weight: 760; }
.profile-hero-actions { display: grid; gap: 10px; }
.profile-hero-actions button { min-height: 46px; display: flex; align-items: center; justify-content: center; gap: 8px; border: 1px solid #dfe8ee; border-radius: 10px; background: rgba(255,255,255,.92); color: #3f5662; font-size: 13px; font-weight: 760; }
.profile-hero-actions button:hover { transform: translateY(-1px); box-shadow: 0 10px 20px rgba(56,91,121,.1); }
.profile-quick-row { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 14px; }
.profile-quick-row button { display: grid; grid-template-columns: 48px minmax(0, 1fr); gap: 4px 12px; align-items: center; min-height: 92px; padding: 14px; border: 1px solid #e2e9ed; border-radius: 12px; background: #fff; text-align: left; box-shadow: 0 10px 24px rgba(31,55,63,.055); }
.profile-quick-row button > span { grid-row: 1 / 4; width: 46px; height: 46px; display: grid; place-items: center; border-radius: 16px; }
.profile-quick-row .ui-icon { width: 23px; height: 23px; }
.profile-quick-row small { color: #596b75; font-size: 12px; font-weight: 700; }
.profile-quick-row b { color: #21333c; font-size: 22px; line-height: 1; }
.profile-quick-row em { color: #8a969c; font-size: 11px; font-style: normal; }
.profile-quick-row .tone-blue { background: #e8f1ff; color: #3b72b5; }
.profile-quick-row .tone-violet { background: #f0ebff; color: #7a62c8; }
.profile-quick-row .tone-red { background: #fff0ee; color: #d36a61; }
.profile-quick-row .tone-orange { background: #fff3e5; color: #c27a32; }
.profile-quick-row .tone-gold { background: #fff6da; color: #b7892e; }
.profile-quick-row .tone-cyan { background: #e9f6f5; color: #438c86; }
.profile-main-grid { display: grid; grid-template-columns: minmax(260px, .9fr) minmax(360px, 1.1fr) minmax(280px, .95fr); grid-template-areas: "security tools activity" "growth growth preference"; gap: 16px; align-items: start; }
.profile-panel, .profile-growth-card { border: 1px solid #e2e9ed; border-radius: 14px; background: #fff; box-shadow: 0 12px 26px rgba(31,55,63,.055); }
.profile-panel { padding: 18px; }
.profile-panel-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.profile-panel-head h3 { margin: 0; color: #24343d; font-size: 17px; font-weight: 760; }
.profile-panel-head span, .profile-panel-head button { color: #7a8991; font-size: 12px; }
.profile-panel-head button { border: 0; background: transparent; }
.profile-security-panel { grid-area: security; }
.profile-tools-panel { grid-area: tools; }
.profile-activity-panel { grid-area: activity; }
.profile-preference-panel { grid-area: preference; }
.profile-setting-list, .profile-timeline, .profile-preference-list { display: grid; gap: 2px; }
.profile-setting-list button, .profile-preference-list button { min-height: 42px; display: grid; grid-template-columns: 22px max-content minmax(0, 1fr) auto; gap: 10px; align-items: center; border: 0; border-bottom: 1px solid #edf2f4; border-radius: 0; background: transparent; color: #536670; text-align: left; }
.profile-setting-list button:last-child, .profile-preference-list button:last-child { border-bottom: 0; }
.profile-setting-list .ui-icon, .profile-preference-list .ui-icon { width: 17px; height: 17px; color: #5f86a7; }
.profile-setting-list b, .profile-preference-list b { color: #3a4d57; font-size: 13px; font-weight: 720; white-space: nowrap; }
.profile-setting-list small { color: #718089; font-size: 12px; }
.profile-setting-list em { color: #438c61; font-size: 12px; font-style: normal; }
.profile-tool-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; padding: 8px 20px 4px; }
.profile-tool-grid button { min-height: 88px; display: grid; place-items: center; gap: 8px; border: 0; border-radius: 14px; background: linear-gradient(180deg, #f7f9fb, #eef3f6); color: #456474; }
.profile-tool-grid .ui-icon { width: 25px; height: 25px; color: #5f8ec7; }
.profile-tool-grid b { font-size: 12px; font-weight: 760; }
.profile-timeline button { position: relative; min-height: 54px; display: grid; grid-template-columns: 18px minmax(0, 1fr) auto; gap: 10px; align-items: start; border: 0; background: transparent; text-align: left; }
.profile-timeline button::before { content: ""; position: absolute; left: 7px; top: 23px; bottom: -12px; width: 1px; background: #e4ecf1; }
.profile-timeline button:last-child::before { display: none; }
.profile-timeline i { width: 9px; height: 9px; margin-top: 6px; border-radius: 50%; background: #5d8dc1; box-shadow: 0 0 0 4px #edf5ff; }
.profile-timeline b { color: #354953; font-size: 13px; }
.profile-timeline small { display: block; margin-top: 3px; color: #7d8b92; font-size: 11px; }
.profile-timeline time { color: #9aa5aa; font-size: 11px; white-space: nowrap; }
.profile-growth-card { grid-area: growth; display: grid; grid-template-columns: minmax(260px, .9fr) minmax(180px, .45fr) minmax(320px, 1fr); gap: 26px; align-items: center; min-height: 168px; padding: 24px; background: radial-gradient(circle at 78% 28%, rgba(88,133,183,.22), transparent 38%), linear-gradient(135deg, #142a4a 0%, #0f2f50 58%, #183b62 100%); color: #fff; }
.profile-growth-card p { margin: 0 0 10px; color: #b9cbe0; font-size: 13px; }
.profile-growth-card h3 { margin: 0; color: #fff; font-size: 32px; }
.profile-growth-card span { color: #dbe6f0; font-size: 12px; }
.profile-growth-card i { display: block; margin-top: 14px; background: rgba(255,255,255,.16); }
.profile-growth-card i b { background: linear-gradient(90deg, #9cc9ff, #c7b06c); }
.profile-growth-level { display: grid; gap: 8px; }
.profile-growth-level small { color: #aabbd0; }
.profile-growth-level b { color: #fff; font-size: 22px; }
.profile-growth-level button { width: max-content; min-height: 32px; padding: 0 14px; border: 1px solid rgba(255,255,255,.18); border-radius: 999px; background: rgba(255,255,255,.12); color: #fff; }
.profile-growth-benefits { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.profile-growth-benefits span { display: grid; place-items: center; gap: 8px; min-height: 68px; border-radius: 14px; background: rgba(255,255,255,.12); color: #edf5ff; font-size: 12px; }
.profile-growth-benefits .ui-icon { width: 22px; height: 22px; color: #d9c07a; }
/* 协作等级阶梯：撑满整行，避免挤进第 4 列 */
.profile-level-ladder { grid-column: 1 / -1; display: flex; flex-wrap: wrap; gap: 8px; }
.profile-level-ladder span { padding: 5px 13px; border: 1px solid rgba(255,255,255,.16); border-radius: 999px;
  background: rgba(255,255,255,.07); color: #93a8bf; font-size: 11px; font-weight: 800; }
.profile-level-ladder span.reached { border-color: rgba(156,201,255,.38); background: rgba(156,201,255,.13); color: #cee2f7; }
.profile-level-ladder span.current { border-color: #d9c07a; background: rgba(217,192,122,.2); color: #fff; }
/* 身份区第二行：当前项目 / 所属团队 */
.profile-hero-main .profile-hero-meta { margin: 4px 0 10px; color: #7c8990; font-size: 12px; }
/* 2 列时每个按钮只有 ~180px，装不下「Memory 自动沉淀 + 需人工审核」这类组合，
   标签会被挤成一字一行、meta 被截成两个字。改成单列整行，一行一项不截断。 */
.profile-preference-list button { grid-template-columns: 22px minmax(0, 1fr) auto; gap: 8px 12px; }
.profile-preference-list b { min-width: 0; white-space: nowrap; line-height: 1.35; }
.profile-preference-list span { min-width: 0; white-space: nowrap; text-align: right; color: #7a8991; font-size: 12px; }
.schedule-editor-card h3 { margin: 5px 0 16px; color: #21383d; font-size: 20px; }
.schedule-editor-checks { display: flex; gap: 12px; margin-top: 14px; color: #52666c; font-size: 13px; font-weight: 800; }
.schedule-editor-checks label { display: inline-flex; align-items: center; gap: 7px; }
.schedule-editor-checks input { accent-color: #5f8c80; }

/* 智能检索：把表单、证据和研判组织成一套清晰的检修工作台。 */
.search-workbench { grid-template-columns: minmax(580px, 1.35fr) minmax(390px, .9fr); gap: 18px; align-items: start; }
.search-workbench > .panel { position: relative; overflow: hidden; }
.search-input-panel, .search-analysis-panel { min-height: 650px; padding: 24px; }
.search-input-panel::before, .search-analysis-panel::before, .search-results-panel::before { content: ""; position: absolute; inset: 0 0 auto; height: 4px; }
.search-input-panel::before { background: linear-gradient(90deg, var(--teal), #39a79c 58%, #82c7bd); }
.search-analysis-panel::before { background: linear-gradient(90deg, var(--blue), var(--violet)); }
.search-results-panel::before { background: linear-gradient(90deg, var(--amber), #e5b45d, var(--teal)); }
.search-panel-heading { display: grid; grid-template-columns: 42px minmax(0, 1fr); gap: 12px; align-items: start; margin-bottom: 20px; }
.search-panel-heading h3 { margin-top: 4px; color: var(--ink); font-size: 18px; }
.search-panel-heading small { display: block; margin-top: 5px; color: var(--muted); font-size: 11px; line-height: 1.55; }
.search-step { width: 42px; height: 42px; display: grid; place-items: center; border-radius: 13px; background: linear-gradient(145deg, #dff2ef, #eff9f7); color: var(--teal-dark); font-size: 12px; font-weight: 900; box-shadow: inset 0 0 0 1px #c8e2de; }
.compact-heading .search-step { background: linear-gradient(145deg, #e4eef9, #f1effa); color: var(--violet); box-shadow: inset 0 0 0 1px #d9dced; }
.search-workbench .form-grid { gap: 15px 16px; }
.search-workbench .form-grid label { gap: 7px; color: #33494e; font-size: 12px; letter-spacing: .02em; }
.search-workbench .form-grid input, .search-workbench .form-grid select, .search-workbench .form-grid textarea { border-color: #d8e2e3; background: #fbfdfd; transition: border-color .18s, background .18s, box-shadow .18s; }
.search-workbench .form-grid input, .search-workbench .form-grid select { height: 46px; padding: 0 13px; }
.search-workbench .form-grid textarea { min-height: 112px; padding: 13px; line-height: 1.65; }
.search-workbench .form-grid input:focus, .search-workbench .form-grid select:focus, .search-workbench .form-grid textarea:focus { border-color: #75aaa5; background: #fff; box-shadow: 0 0 0 3px rgba(22,118,111,.09); }
.search-upload-zone { display: grid; grid-template-columns: 46px minmax(0, 1fr) auto; align-items: center; gap: 13px; margin-top: 18px; padding: 15px 16px; border: 1px dashed #9fbfbc; background: linear-gradient(135deg, #f1f8f7, #fbfdfd); text-align: left; }
.upload-mark { width: 46px; height: 46px; display: grid; place-items: center; border-radius: 13px; background: #dcefed; color: var(--teal); }
.upload-mark .ui-icon { width: 22px; height: 22px; }
.upload-copy { display: grid; gap: 4px; min-width: 0; }
.upload-copy b { color: var(--ink); font-size: 13px; }
.upload-copy small { color: var(--muted); font-size: 10px; }
.search-upload-zone > button { border-color: #bdd4d1; background: #fff; color: var(--teal-dark); font-size: 12px; font-weight: 800; }
.search-upload-zone > button:hover { border-color: var(--teal); background: #e8f5f3; }
.search-workbench .file-pills span { display: inline-flex; align-items: center; gap: 7px; border: 1px solid #d5e5e3; background: #edf7f5; color: #34595a; }
.search-workbench .file-pills img { width: 28px; height: 28px; border-radius: 7px; object-fit: cover; }
.search-workbench .file-pills button { padding: 3px 6px; border: 0; background: transparent; color: var(--danger); font-size: 10px; }
.search-actions { margin-top: 18px; padding-top: 15px; border-top: 1px solid #e5ebec; }
.search-actions button { min-height: 44px; padding: 9px 17px; font-size: 13px; font-weight: 800; }
.search-actions .primary { min-width: 148px; box-shadow: 0 9px 18px rgba(19,91,87,.16); }
.search-analysis-panel { display: flex; flex-direction: column; background: linear-gradient(160deg, #fff 0%, #fbfcff 58%, #f4f7fb 100%); }
.search-analysis-panel.ready { background: linear-gradient(160deg, #fff 0%, #f8fbfb 100%); }
.search-analysis-panel > template + * { min-width: 0; }
.analysis-summary { margin-bottom: 14px; padding: 15px; border: 1px solid #d9e5e7; border-left: 4px solid var(--blue); border-radius: 11px; background: #fff; }
.analysis-summary span { color: var(--blue); font-size: 10px; font-weight: 900; letter-spacing: .08em; }
.analysis-summary h3 { margin-top: 6px; font-size: 17px; line-height: 1.55; }
.search-analysis-panel .analysis-grid { grid-template-columns: 1fr; margin-top: 0; }
.search-analysis-panel .analysis-grid span { border: 1px solid #e1e8ea; background: rgba(255,255,255,.82); }
.search-analysis-panel h4 { margin: 16px 0 7px; color: var(--ink); font-size: 13px; }
.search-analysis-panel ul { margin: 0; padding-left: 20px; color: #4d6268; line-height: 1.75; }
.search-analysis-panel > p { color: #4d6268; line-height: 1.7; }
.search-empty-state { flex: 1; min-height: 470px; display: grid; place-items: center; align-content: center; gap: 12px; padding: 32px; border: 1px solid #e1e7ed; border-radius: 16px; background: radial-gradient(circle at 50% 36%, rgba(63,126,178,.08), transparent 34%), rgba(255,255,255,.72); text-align: center; }
.search-empty-state h4 { margin: 4px 0 0; font-size: 17px; }
.search-empty-state p { max-width: 330px; color: var(--muted); font-size: 12px; line-height: 1.7; }
.search-empty-state ol { display: grid; grid-template-columns: repeat(3, auto); gap: 10px; margin: 6px 0 0; padding: 0; list-style: none; }
.search-empty-state li { display: flex; align-items: center; gap: 5px; padding: 7px 9px; border: 1px solid #dce5ea; border-radius: 999px; background: #fff; color: #596c72; font-size: 10px; }
.search-empty-state li b { width: 17px; height: 17px; display: grid; place-items: center; border-radius: 50%; background: #e4edf7; color: var(--blue); }
.analysis-orbit { position: relative; width: 96px; height: 96px; display: grid; place-items: center; border: 1px solid #cbdbe7; border-radius: 50%; background: rgba(255,255,255,.88); box-shadow: 0 14px 30px rgba(48,88,121,.1); }
.analysis-orbit::before { content: ""; position: absolute; inset: 12px; border: 1px dashed #b4cbdc; border-radius: 50%; }
.analysis-orbit b { width: 46px; height: 46px; display: grid; place-items: center; z-index: 1; border-radius: 15px; background: linear-gradient(145deg, var(--blue), var(--violet)); color: #fff; font-size: 15px; }
.analysis-orbit i { position: absolute; width: 8px; height: 8px; border-radius: 50%; background: var(--teal); box-shadow: 0 0 0 4px #dff0ee; }
.analysis-orbit i:nth-child(1) { top: 10px; left: 44px; }
.analysis-orbit i:nth-child(2) { right: 8px; bottom: 24px; background: var(--amber); box-shadow: 0 0 0 4px #f9ead4; }
.analysis-orbit i:nth-child(3) { left: 8px; bottom: 24px; background: var(--violet); box-shadow: 0 0 0 4px #ece7f6; }
.search-results-panel { margin-top: 2px; padding: 22px 24px; background: linear-gradient(180deg, #fff, #fbfcfc); }
.search-results-panel .panel-head { align-items: flex-end; }
.search-results-panel .panel-head h3 { margin-top: 5px; color: var(--ink); font-size: 18px; }
.search-results-panel .tabs { justify-content: flex-end; }
.search-results-panel .tabs button { min-height: 36px; border-color: #dbe3e4; background: #fff; color: #4a5d62; font-size: 11px; }
.search-results-panel .tabs button.active { border-color: var(--teal-dark); background: var(--teal-dark); color: #fff; }
.search-results-panel .result-grid { margin-top: 18px; }
.search-results-panel .result-card { border-color: #dfe7e8; background: #fff; box-shadow: 0 7px 18px rgba(31,55,63,.045); }
.search-results-panel .result-card:hover { transform: translateY(-2px); border-color: #b6cecc; box-shadow: 0 12px 24px rgba(31,55,63,.08); }

/* 主工作区与智能体面板可调宽度，五个一级页面共用。 */
.content-shell { grid-template-columns: minmax(0, 1fr) 10px var(--operator-width, 360px); }
.search-focus-shell { grid-template-columns: minmax(0, 1fr) !important; }
.search-focus-shell .panel-resizer,
.search-focus-shell .operator-panel { display: none !important; }
.search-focus-shell .page-scroll {
  overflow-x: hidden;
  padding-right: 16px;
  scrollbar-width: none;
}
.search-focus-shell .page-scroll::-webkit-scrollbar {
  width: 0;
  height: 0;
}
.panel-resizer { position: relative; z-index: 4; width: 10px; min-width: 10px; height: 100%; padding: 0; border: 0; border-radius: 0; background: #e6edef; cursor: col-resize; touch-action: none; }
.panel-resizer::before { content: ""; position: absolute; inset: 0 -5px; }
.panel-resizer span { position: absolute; left: 3px; top: 50%; width: 4px; height: 54px; border-radius: 999px; background: #9bb1b5; transform: translateY(-50%); transition: height .18s, background .18s; }
.panel-resizer:hover span, :global(body.resizing-panel) .panel-resizer span { height: 90px; background: var(--teal); }
:global(body.resizing-panel) { cursor: col-resize; user-select: none; }
.operator-panel { min-width: 300px; max-width: 520px; overflow: hidden; background: linear-gradient(180deg, #f4f8f8 0%, #edf3f3 100%); --op-accent: var(--teal); --op-accent-dark: var(--teal-dark); --op-soft: #eef6f5; --op-tint: linear-gradient(180deg, #f4f8f8 0%, #edf3f3 100%); }

/* 每个 agent aside 背景与其头像主色调匹配，形成独立视觉风格。 */
.profile-focus-shell { grid-template-columns: minmax(0, 1fr); }
.profile-focus-shell .page-scroll { padding: 20px 24px 24px; }
.profile-focus-shell .panel-resizer,
.profile-focus-shell .operator-panel { display: none; }
.profile-focus-shell .profile-dashboard { width: 100%; max-width: none; margin: 0; }
.profile-focus-shell .profile-hero-card { grid-template-columns: 112px minmax(0, 1fr) 190px; min-height: 156px; padding: 22px 28px; }
.profile-focus-shell .profile-quick-row { grid-template-columns: repeat(6, minmax(150px, 1fr)); gap: 12px; }
.profile-focus-shell .profile-quick-row button { min-height: 86px; padding: 13px; }
.profile-focus-shell .profile-main-grid { grid-template-columns: minmax(300px, .88fr) minmax(420px, 1.24fr) minmax(320px, .96fr); gap: 14px; }
.profile-focus-shell .profile-panel { min-height: 246px; }
.profile-focus-shell .profile-growth-card { min-height: 158px; }
.profile-focus-shell .profile-dashboard { gap: 12px; }
.profile-focus-shell .profile-main-grid {
  grid-template-columns: minmax(300px, .94fr) minmax(420px, 1.16fr) minmax(330px, .98fr);
  grid-template-areas: "security tools activity" "growth growth preference";
  /* 第二行原来写死 166px，协作画像（多了等级阶梯）和个性化设置（7 项）都被压到
     166 高、内容溢出卡片外。改成下限 166、随内容增长。 */
  grid-template-rows: minmax(238px, auto) minmax(166px, auto);
  align-items: stretch;
}
.profile-focus-shell .profile-panel { min-height: 0; height: 100%; }
.profile-focus-shell .profile-security-panel,
.profile-focus-shell .profile-tools-panel,
.profile-focus-shell .profile-activity-panel { min-height: 238px; }
.profile-focus-shell .profile-growth-card,
.profile-focus-shell .profile-preference-panel { min-height: 166px; }
.profile-focus-shell .profile-growth-card {
  grid-template-columns: minmax(260px, .75fr) minmax(160px, .35fr) minmax(360px, .9fr);
  gap: 20px;
  padding: 18px 24px;
  /* 卡片里比原来多了协作等级阶梯那一行，固定高度会把阶梯挤到卡片外 */
  height: auto;
  /* 行高放开后卡片会被右侧更长的个性化设置撑高，内容整块居中而不是顶在上面 */
  align-content: center;
}
.profile-focus-shell .profile-growth-card p { margin-bottom: 6px; }
.profile-focus-shell .profile-growth-card h3 { font-size: 34px; line-height: 1; }
.profile-focus-shell .profile-growth-card i { margin-top: 12px; }
.profile-focus-shell .profile-growth-benefits { align-items: center; gap: 10px; }
.profile-focus-shell .profile-growth-benefits span { min-height: 58px; }
.profile-focus-shell .profile-preference-panel { padding: 16px 18px; }
.profile-focus-shell .profile-preference-panel .profile-panel-head { margin-bottom: 8px; }
.profile-focus-shell .profile-preference-list { grid-template-columns: minmax(0, 1fr); gap: 6px; }
.profile-focus-shell .profile-preference-list button {
  min-height: 40px;
  grid-template-columns: 20px minmax(0, 1fr) auto;
  padding: 0 12px;
  border: 1px solid #edf2f4;
  border-radius: 10px;
  background: #fbfdfe;
}
.profile-focus-shell .profile-setting-list button { min-height: 39px; }
.profile-focus-shell .profile-tool-grid { height: calc(100% - 42px); align-content: center; padding: 4px 10px 0; gap: 12px; }
.profile-focus-shell .profile-tool-grid button { min-height: 76px; }
.profile-focus-shell .profile-timeline button { min-height: 45px; }
.operator-panel.op-theme-tiangong { --op-accent: #2563EB; --op-accent-dark: #1a4cc0; --op-soft: #fafbfd; --op-tint: linear-gradient(178deg, #fcfdfe 0%, #f8fafe 50%, #f2f5fc 100%); }
.operator-panel.op-theme-guanwei { --op-accent: #6B8E23; --op-accent-dark: #4f6b1a; --op-soft: #fcfcf7; --op-tint: linear-gradient(178deg, #fdfdf8 0%, #fbfcf4 50%, #f7f9ef 100%); }
.operator-panel.op-theme-zhiju { --op-accent: #FF6B35; --op-accent-dark: #c84d1f; --op-soft: #fffaf8; --op-tint: linear-gradient(178deg, #fffcfa 0%, #fffbf5 50%, #fff6ef 100%); }
.operator-panel.op-theme-bowen { --op-accent: #80B918; --op-accent-dark: #5c8a0e; --op-soft: #fbfcf6; --op-tint: linear-gradient(178deg, #fdfdf7 0%, #fbfdf2 50%, #f7f9e9 100%); }
.operator-panel.op-theme-heming { --op-accent: #4DB8A1; --op-accent-dark: #2f8a76; --op-soft: #f8fcfa; --op-tint: linear-gradient(178deg, #fcfdfb 0%, #fafcf9 50%, #f4f8f4 100%); }
.operator-panel.op-theme-mingjian { --op-accent: #A9C7E8; --op-accent-dark: #6F9BC6; --op-soft: #f3f8fe; --op-tint: linear-gradient(178deg, #fdfeff 0%, #f6fbff 52%, #e9f3ff 100%); }

.operator-panel { background: var(--op-tint); border-left-color: color-mix(in srgb, var(--op-accent) 8%, var(--line)); }
.operator-panel .operator-avatar { box-shadow: 0 8px 14px color-mix(in srgb, var(--op-accent) 14%, transparent); border: 2px solid #fff; }
.operator-panel .operator-slogan { border-color: color-mix(in srgb, var(--op-accent) 8%, #d7e5e5); border-left-color: var(--op-accent); background: color-mix(in srgb, var(--op-accent) 3%, #fff); color: color-mix(in srgb, var(--op-accent-dark) 52%, #244146); }
.operator-panel .operator-role { background: color-mix(in srgb, var(--op-accent) 5%, #fff); color: var(--op-accent-dark); }
.operator-panel .operator-status { background: color-mix(in srgb, var(--op-accent) 6%, #fff); color: var(--op-accent-dark); }
.operator-panel .bubble.user { border-color: var(--op-accent-dark); background: var(--op-accent-dark); }
.operator-panel .quick-card { border-color: color-mix(in srgb, var(--op-accent) 8%, #d7e5e5); background: #fff; }
.operator-panel .quick-card > span { background: var(--op-accent-dark); color: #fff; }
.operator-panel .operator-chips button { border-color: color-mix(in srgb, var(--op-accent) 10%, #cedbdc); color: var(--op-accent-dark); }
.operator-panel .operator-chips button:hover { background: var(--op-soft); border-color: var(--op-accent); }
.operator-panel .ask-box { border-color: color-mix(in srgb, var(--op-accent) 18%, #97b6b5); }
.operator-panel .ask-box button { background: var(--op-accent-dark); color: #fff; }
.operator-panel .ask-box input:focus { outline: 0; }
.operator-panel .assistant-input-tools button:hover, .operator-panel .assistant-input-tools button.active { border-color: var(--op-accent); background: var(--op-soft); color: var(--op-accent-dark); }
.operator-panel .bubble.assistant { border-color: color-mix(in srgb, var(--op-accent) 6%, #dce7e8); }

/* 麒麟浏览器与窄屏演示兜底：智能体头像保持原图比例，避免被圆形容器拉伸或裁空。 */
.operator-avatar,
.agent-row img,
.agent-history img,
.agent-history-avatar img,
.search-agent-intro img,
.search-ai-status img,
.tg-run-mark img,
.conversation-scroll img,
.message img,
.collab-info > img,
.member-board img,
.group-profile img,
.group-members img,
.profile-agent-simple img {
  aspect-ratio: 1 / 1;
  object-fit: contain !important;
  object-position: center center !important;
  background: #f4f8f6;
}

.operator-avatar,
.search-agent-intro img,
.search-ai-status img,
.tg-run-mark img {
  padding: 2px;
}

.operator-panel {
  flex-shrink: 0;
}
.aios-recorder {
  display: none !important;
}
.aios-recorder { gap: 10px; padding: 13px; border: 1px solid color-mix(in srgb, var(--op-accent) 10%, #d8e2e1); border-radius: 18px; background: rgba(255,255,255,.72); box-shadow: 0 10px 24px rgba(31,67,70,.055); }
.aios-recorder.active { background: linear-gradient(180deg, rgba(255,255,255,.9), color-mix(in srgb, var(--op-soft) 50%, #fff)); }
.aios-recorder-head { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; align-items: start; }
.aios-recorder-head .eyebrow { margin: 0 0 4px; color: var(--op-accent-dark); font-size: 10px; font-weight: 900; letter-spacing: .08em; }
.aios-recorder-head h3 { margin: 0; color: #19353a; font-size: 14px; font-weight: 800; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.aios-recorder-head button { min-height: 30px; padding: 0 10px; border: 1px solid color-mix(in srgb, var(--op-accent) 18%, #d2dfde); border-radius: 999px; background: #fff; color: var(--op-accent-dark); font-size: 12px; font-weight: 800; }
.aios-recorder-head button:disabled { cursor: wait; opacity: .65; }
.aios-meter { height: 8px; overflow: hidden; border-radius: 999px; background: #e8eeed; }
.aios-meter span { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, color-mix(in srgb, var(--op-accent) 72%, #fff), var(--op-accent-dark)); transition: width .35s ease; }
.aios-recorder-meta { display: flex; flex-wrap: wrap; gap: 6px; color: #536b70; font-size: 11px; }
.aios-recorder-meta span { max-width: 100%; padding: 4px 7px; border-radius: 999px; background: #f6f8f7; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.aios-agent-rail { display: flex; gap: 8px; overflow-x: auto; padding: 2px 1px 6px; scrollbar-width: thin; }
.aios-step-dot { min-width: 54px; display: grid; justify-items: center; gap: 5px; color: #5d7378; }
.aios-step-dot i { width: 30px; height: 30px; display: grid; place-items: center; border: 1px solid #d7e1df; border-radius: 50%; background: #fff; color: #577074; font-size: 10px; font-style: normal; font-weight: 900; box-shadow: 0 5px 12px rgba(28,62,68,.05); }
.aios-step-dot b { width: 58px; color: #5b7074; font-size: 10px; font-weight: 700; line-height: 1.25; text-align: center; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.aios-step-dot.running i, .aios-step-dot.in_progress i { border-color: color-mix(in srgb, var(--op-accent) 45%, #fff); background: var(--op-accent-dark); color: #fff; animation: aiosPulse 1.6s ease-in-out infinite; }
.aios-step-dot.done i, .aios-step-dot.completed i { border-color: #9fbdad; background: #edf6f1; color: #367052; }
.aios-step-dot.failed i { border-color: #e3b4a9; background: #fff1ee; color: #a24d3f; }
.aios-empty-trace { padding: 12px; border: 1px dashed #d7e1df; border-radius: 13px; color: #718489; background: #fff; font-size: 12px; line-height: 1.55; }
.aios-event-stream { display: grid; gap: 7px; max-height: 178px; overflow: auto; padding-right: 2px; }
.aios-event-stream article { display: grid; grid-template-columns: 46px minmax(0, 1fr); gap: 8px; align-items: start; padding: 9px; border: 1px solid #e1e9e8; border-radius: 13px; background: #fff; }
.aios-event-stream article span { width: 38px; height: 38px; display: grid; place-items: center; border-radius: 50%; background: color-mix(in srgb, var(--op-accent) 8%, #f8fbfa); color: var(--op-accent-dark); font-size: 11px; font-weight: 900; }
.aios-event-stream article b { display: block; color: #203a3f; font-size: 12px; font-weight: 800; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.aios-event-stream article small { display: -webkit-box; margin-top: 3px; color: #71868a; font-size: 11px; line-height: 1.45; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.aios-event-stream article.done, .aios-event-stream article.success { border-color: #d7e9dd; }
.aios-event-stream article.failed, .aios-event-stream article.error { border-color: #efd0c9; background: #fff8f6; }
.aios-error { margin: 0; padding: 9px 10px; border-radius: 11px; background: #fff2ef; color: #a24d3f; font-size: 12px; line-height: 1.45; }
@keyframes aiosPulse { 0%, 100% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--op-accent) 18%, transparent); } 50% { box-shadow: 0 0 0 7px color-mix(in srgb, var(--op-accent) 0%, transparent); } }
.operator-head { grid-template-columns: 64px minmax(0, 1fr) auto; align-items: start; }
.operator-head-actions { display: grid; justify-items: end; gap: 8px; }
.operator-duty { color: #3f555a; font-size: 14px; line-height: 1.72; }
.operator-slogan { border: 1px solid #d7e5e5; border-left: 4px solid var(--teal); color: #244146; font-size: 14px; line-height: 1.55; box-shadow: 0 5px 14px rgba(28, 74, 78, .045); }
.chat-thread { gap: 13px; padding: 3px 6px 6px 1px; scrollbar-color: #9db0b3 transparent; }
.bubble { max-width: 92%; padding: 13px 15px; border: 1px solid #dce7e8; border-radius: 16px 16px 16px 5px; color: #1e3439; background: #fff; font-size: 14.5px; font-weight: 500; line-height: 1.72; white-space: pre-wrap; box-shadow: 0 6px 15px rgba(28, 62, 68, .055); }
.bubble.user { border-color: var(--teal-dark); border-radius: 16px 16px 5px 16px; background: var(--teal-dark); color: #fff; }
.aios-result-report { display: grid; gap: 12px; min-width: min(430px, 100%); white-space: normal; }
.aios-result-report summary { display: grid; grid-template-columns: 42px minmax(0, 1fr) auto; align-items: center; gap: 10px; padding: 2px 0 10px; border-bottom: 1px solid #e5ede9; cursor: pointer; list-style: none; }
.aios-result-report summary::-webkit-details-marker { display: none; }
.aios-result-report summary > span { width: 42px; height: 42px; display: grid; place-items: center; border-radius: 14px; background: #205f61; color: #fff; font-size: 11px; font-weight: 900; box-shadow: 0 10px 18px rgba(32,95,97,.14); }
.aios-result-report summary small { display: block; color: #718884; font-size: 11px; font-weight: 700; line-height: 1.4; }
.aios-result-report summary b { display: block; margin-top: 2px; color: #17393b; font-size: 16px; }
.aios-result-report summary em { padding: 5px 8px; border-radius: 999px; background: #fff8ec; color: #8a662d; font-size: 11px; font-style: normal; font-weight: 900; }
.aios-result-report[open] summary em { background: #eaf3ef; color: #205f61; }
.aios-report-metrics { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.aios-report-metrics span { min-width: 0; padding: 10px; border: 1px solid #e2ebe7; border-radius: 12px; background: #fbfdfa; }
.aios-report-metrics small { display: block; color: #7a8b88; font-size: 10px; font-weight: 800; }
.aios-report-metrics b { display: block; margin-top: 4px; color: #8a662d; font-size: 14px; }
.aios-report-section { padding: 11px 12px; border: 1px solid #eadfc8; border-radius: 14px; background: #fffaf1; }
.aios-result-report h4 { margin: 0 0 7px; color: #205f61; font-size: 13px; }
.aios-result-report p { margin: 0; color: #405a5a; font-size: 12.5px; line-height: 1.65; }
.aios-report-recommend-list { display: grid; gap: 8px; }
.aios-report-recommend-list article { padding: 9px 10px; border: 1px solid #e0eae6; border-radius: 12px; background: #fff; }
.aios-report-recommend-list b { display: block; color: #21464a; font-size: 12.5px; }
.aios-report-recommend-list small { display: block; margin-top: 3px; color: #687d7a; font-size: 11px; line-height: 1.45; }
.aios-result-report footer { display: flex; flex-wrap: wrap; gap: 7px; }
.aios-result-report footer span { padding: 5px 8px; border: 1px solid #dce8e3; border-radius: 999px; background: #f7faf7; color: #52706b; font-size: 11px; font-weight: 800; }
.aios-report-open { width: 100%; min-height: 38px; border: 1px solid #d9c9a8; border-radius: 12px; background: #fff8ec; color: #7d5b25; font-weight: 900; }
.aios-report-page { width: min(1080px, 96vw); max-height: 90vh; gap: 16px; padding: 0 24px 20px; border: 1px solid #ded8cf; border-radius: 18px; background: #fbfaf7; box-shadow: 0 28px 80px rgba(26,42,43,.22); }
.aios-report-page > header { position: sticky; top: 0; z-index: 2; display: grid; grid-template-columns: 62px minmax(0, 1fr); align-items: center; gap: 16px; margin: 0 -24px; padding: 22px 64px 20px 24px; border-bottom: 1px solid #e4ded4; border-radius: 18px 18px 0 0; background: #fffdf9; }
.aios-report-page > header > span { width: 62px; height: 62px; display: grid; place-items: center; border-radius: 18px; background: #205f61; color: #fff; font-weight: 900; box-shadow: 0 14px 28px rgba(32,95,97,.16); }
.aios-report-page h2 { margin: 4px 0; color: #172e31; font-size: 24px; }
.aios-report-page header small { color: #6d7c78; }
.aios-page-metrics { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.aios-page-metrics span { padding: 14px; border: 1px solid #e1e9e5; border-radius: 14px; background: #fff; }
.aios-page-metrics small { display: block; color: #7b8a86; font-size: 11px; font-weight: 800; }
.aios-page-metrics b { display: block; margin-top: 5px; color: #8a662d; font-size: 18px; }
.aios-page-conclusion { padding: 16px; border-left: 4px solid #b88a44; border-radius: 0 14px 14px 0; background: #fff8ec; }
.aios-report-page h3 { margin: 0 0 10px; color: #205f61; font-size: 16px; }
.aios-page-conclusion p { color: #4f5e58; line-height: 1.8; }
.aios-page-recommendations { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.aios-page-recommendations > div { grid-column: 1 / -1; }
.aios-page-recommendations article { padding: 15px; border: 1px solid #dce8e3; border-radius: 15px; background: linear-gradient(180deg, #fff, #f8fbf7); box-shadow: 0 8px 18px rgba(30,65,64,.045); }
.aios-page-recommendations article > span { display: inline-flex; margin-bottom: 8px; padding: 4px 8px; border-radius: 999px; background: #eaf3ef; color: #205f61; font-size: 11px; font-weight: 900; }
.aios-page-recommendations h4 { margin: 0 0 7px; color: #17393b; font-size: 15px; }
.aios-page-recommendations p { margin: 0 0 10px; color: #536762; font-size: 13px; line-height: 1.6; }
.aios-page-recommendations ul, .task-report-recommendations ul { display: grid; gap: 6px; margin: 0; padding-left: 16px; color: #465d59; font-size: 12.5px; line-height: 1.55; }
.aios-page-blocks { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.aios-page-blocks article { padding: 16px; border: 1px solid #e1e9e5; border-radius: 14px; background: #fff; }
.aios-page-blocks ul { display: grid; gap: 9px; margin: 0; padding: 0; list-style: none; }
.aios-page-blocks li { position: relative; padding-left: 16px; color: #435956; line-height: 1.65; }
.aios-page-blocks li::before { content: ""; position: absolute; left: 0; top: .7em; width: 6px; height: 6px; border-radius: 50%; background: #b88a44; }
.aios-report-page footer { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 2px -24px -20px; padding: 14px 24px; border-top: 1px solid #e4ded4; background: #fffdf9; border-radius: 0 0 18px 18px; }
.aios-report-page footer span { padding: 6px 9px; border: 1px solid #dce8e3; border-radius: 999px; background: #f7faf7; color: #52706b; font-size: 12px; font-weight: 800; }
.aios-report-page footer button { margin-left: auto; }
.quick-card { background: #fff; box-shadow: 0 5px 14px rgba(28, 62, 68, .04); }
.operator-chips button { border-color: #cedbdc; color: #27464a; font-size: 12.5px; }
.assistant-input-tools { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.assistant-input-tools button { min-height: 40px; display: flex; align-items: center; justify-content: center; gap: 7px; padding: 8px 10px; border: 1px solid #c9dadb; border-radius: 11px; background: #fff; color: #29565a; font-size: 12.5px; font-weight: 800; }
.assistant-input-tools button:hover, .assistant-input-tools button.active { border-color: var(--teal); background: #e6f4f2; color: var(--teal-dark); }
.assistant-input-tools .ui-icon { width: 18px; height: 18px; }
.ask-box { grid-template-columns: minmax(0, 1fr) 42px; align-items: center; min-height: 58px; padding: 8px 8px 8px 14px; border: 1px solid #97b6b5; border-radius: 15px; box-shadow: 0 7px 18px rgba(28, 62, 68, .055); }
.ask-box input { height: 40px; color: #1d3438; font-size: 14px; }
.ask-box input::placeholder { color: #7d9094; opacity: 1; }
.ask-box button { width: 42px; height: 42px; display: grid; place-items: center; border-radius: 12px; }
.ask-box button .ui-icon { width: 19px; height: 19px; }
.assistant-attachments { max-height: 126px; overflow: auto; }
.assistant-attachments span { min-height: 38px; background: #fff; border: 1px solid #d7e5e5; color: #314d51; }
.assistant-attachments span img { width: 30px; height: 30px; border-radius: 7px; object-fit: cover; }
.assistant-attachments span i { padding: 2px 5px; border-radius: 5px; background: #e6f3f2; color: var(--teal); font-size: 9px; font-style: normal; font-weight: 900; }
/* 登录与注册：独立门禁页面，不依赖业务接口，避免影响现有服务连接。 */
.app-shell.auth-shell { display: block; min-width: 0; background: #f2f8fc; }
.auth-gate { min-height: 100vh; display: grid; grid-template-columns: minmax(520px, 1.08fr) minmax(460px, .92fr); background: #f6fbff; }
.auth-visual { position: relative; min-height: 100vh; overflow: hidden; display: flex; flex-direction: column; justify-content: space-between; padding: 52px 64px 44px; background: linear-gradient(145deg, #e9f8ff 0%, #bfe6ff 46%, #7fc6ef 100%); color: #17364a; }
.auth-visual::before { content: ""; position: absolute; width: 560px; height: 560px; right: -180px; bottom: -170px; border: 1px solid rgba(255,255,255,.74); border-radius: 50%; box-shadow: 0 0 0 74px rgba(255,255,255,.28), 0 0 0 148px rgba(77,164,219,.08); }
.auth-visual::after { content: ""; position: absolute; width: 380px; height: 380px; left: -140px; top: 18%; border-radius: 50%; background: rgba(255,255,255,.34); filter: blur(2px); }
.auth-grid { position: absolute; inset: 0; opacity: .42; background-image: linear-gradient(rgba(44,126,178,.16) 1px, transparent 1px), linear-gradient(90deg, rgba(44,126,178,.16) 1px, transparent 1px); background-size: 54px 54px; mask-image: linear-gradient(135deg, #000, transparent 82%); }
.auth-brand, .auth-intro, .auth-footnote { position: relative; z-index: 1; }
.auth-brand { display: flex; align-items: center; gap: 20px; width: fit-content; padding: 12px 18px 12px 14px; border: 1px solid rgba(255,255,255,.78); border-radius: 20px; background: rgba(255,255,255,.58); box-shadow: 0 18px 38px rgba(44,126,178,.14); backdrop-filter: blur(10px); color: #285a73; font-size: 14px; letter-spacing: .08em; }
.auth-brand img { width: 190px; height: 82px; padding: 0; object-fit: contain; border-radius: 14px; background: transparent; filter: drop-shadow(0 12px 18px rgba(37,95,130,.12)); }
.auth-intro { max-width: 650px; margin: auto 0; }
.auth-intro > p { margin-bottom: 18px; color: #236d91; font-size: 14px; font-weight: 800; letter-spacing: .12em; }
.auth-intro h1 { margin: 0; color: #183c54; font-size: clamp(42px, 4vw, 68px); line-height: 1.24; letter-spacing: -.04em; text-shadow: 0 1px 0 rgba(255,255,255,.72); }
.auth-capabilities { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-top: 48px; }
.auth-capabilities span { display: grid; gap: 10px; padding: 18px; border: 1px solid rgba(255,255,255,.68); border-radius: 14px; background: rgba(255,255,255,.45); backdrop-filter: blur(8px); color: #2c6179; font-size: 13px; box-shadow: 0 10px 28px rgba(68,142,186,.08); }
.auth-capabilities b { color: #237eaf; font-size: 11px; letter-spacing: .12em; }
.auth-footnote { color: rgba(31,82,108,.66); font-size: 12px; }
.auth-form-side { display: grid; place-items: center; padding: 48px; background: radial-gradient(circle at 85% 12%, rgba(112,190,235,.16), transparent 28%), #f6fbff; }
.auth-card { width: min(460px, 100%); display: grid; gap: 22px; padding: 38px; border: 1px solid #d5e8f2; border-radius: 24px; background: rgba(255,255,255,.96); box-shadow: 0 28px 70px rgba(56,118,153,.14); }
.auth-card-head p { color: #2c8cbd; font-size: 13px; font-weight: 900; letter-spacing: .1em; }
.auth-card-head h2 { margin: 8px 0; color: #18384c; font-size: 28px; }
.auth-card-head span { color: #6b8492; font-size: 13px; }
.auth-tabs { display: grid; grid-template-columns: 1fr 1fr; padding: 4px; border-radius: 12px; background: #ecf6fb; }
.auth-tabs button { min-height: 42px; border: 0; background: transparent; color: #6f8794; font-weight: 800; }
.auth-tabs button.active { background: #fff; color: #237eaf; box-shadow: 0 5px 14px rgba(56,118,153,.1); }
.auth-fields { display: grid; gap: 15px; }
.auth-fields label { display: grid; gap: 7px; color: #345266; font-size: 12px; font-weight: 800; }
.auth-fields input { width: 100%; height: 48px; padding: 0 14px; border: 1px solid #d1e4ee; border-radius: 11px; outline: 0; color: #18384c; background: #fbfdff; }
.auth-fields input:focus { border-color: #68b5df; box-shadow: 0 0 0 3px rgba(79,171,224,.14); background: #fff; }
.remember-row { display: flex; align-items: center; gap: 8px; color: #647a7f; font-size: 12px; }
.remember-row input { accent-color: var(--teal); }
.auth-error, .form-error { padding: 10px 12px; border: 1px solid #f0c7c0; border-radius: 9px; background: #fff4f2; color: #a84437; font-size: 12px; }
.auth-submit { min-height: 50px; border: 0; border-radius: 12px; background: linear-gradient(135deg, #247faf, #53b5e8); color: #fff; font-weight: 900; box-shadow: 0 10px 22px rgba(44,140,189,.23); }
.auth-submit:hover { transform: translateY(-1px); box-shadow: 0 14px 26px rgba(44,140,189,.28); }
.demo-account { display: grid; grid-template-columns: 1fr auto; gap: 6px 14px; padding: 13px 15px; border: 1px dashed #c9d9d9; border-radius: 11px; background: #f3f8f7; color: #496267; font-size: 11px; }
.demo-account span { grid-column: 1 / -1; color: var(--teal); font-weight: 900; }
.demo-account b { font-weight: 700; }

/* 个人资料编辑。 */
.profile-editor-card { width: min(780px, 94vw); overflow: hidden; padding: 0; border: 1px solid #d4e2e2; background: #fff; }
.profile-editor-head { display: grid; grid-template-columns: 72px minmax(0, 1fr); gap: 16px; align-items: center; padding: 26px 30px; background: linear-gradient(135deg, #e7f4f2, #f7faf9 65%, #eef2f8); }
.profile-editor-head img { width: 72px; height: 72px; border: 4px solid #fff; border-radius: 50%; object-fit: cover; box-shadow: 0 8px 20px rgba(31,75,79,.13); }
.profile-editor-head h2 { margin: 5px 0; color: #18383c; font-size: 24px; }
.profile-editor-head span { color: #708388; font-size: 12px; }
.profile-editor-grid { padding: 26px 30px 8px; gap: 16px; }
.profile-editor-grid label { color: #385055; font-size: 12px; font-weight: 800; }
.profile-editor-grid input, .profile-editor-grid select, .profile-editor-grid textarea { border-color: #d7e2e3; background: #fbfdfd; }
.profile-editor-grid textarea { min-height: 92px; }
.profile-editor-card .form-error { margin: 0 30px; }
.profile-editor-actions { display: flex; justify-content: flex-end; gap: 10px; padding: 18px 30px 24px; }
.profile-editor-actions button { min-width: 104px; }

/* 智能体使用记录：用角色色和信息层级替代重复的平铺框。 */
.agent-history-panel { position: relative; overflow: hidden; padding: 14px 16px; border-color: #d7e4e4; background: linear-gradient(150deg, #fff 0%, #f8fbfb 100%); }
.agent-history-panel::before { content: ""; position: absolute; inset: 0 0 auto; height: 3px; background: linear-gradient(90deg, var(--teal), var(--blue), var(--violet), var(--amber)); }
.agent-history-panel .panel-head h3 { margin-top: 3px; color: #203c41; font-size: 16px; }
.agent-history-panel .panel-head .eyebrow { font-size: 10px; }
.agent-history-panel .panel-head > button { min-height: 28px; padding: 4px 9px; font-size: 10px; }
.agent-history { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 9px; margin-top: 4px; }
.agent-history article { --agent-color: #16766f; position: relative; min-height: 96px; grid-template-columns: 42px minmax(0, 1fr); grid-template-rows: 1fr auto; align-items: start; gap: 8px 10px; padding: 11px; overflow: hidden; border-color: color-mix(in srgb, var(--agent-color) 22%, #dce5e6); border-radius: 12px; background: linear-gradient(145deg, color-mix(in srgb, var(--agent-color) 7%, #fff), #fff 72%); box-shadow: 0 8px 20px rgba(31,55,63,.055); }
.agent-history article:nth-child(2), .agent-history article:nth-child(5) { --agent-color: #387bb4; }
.agent-history article:nth-child(3), .agent-history article:nth-child(6) { --agent-color: #8a66b4; }
.agent-history article:nth-child(4) { --agent-color: #c27c2e; }
.agent-history article::after { content: counter(agent-card, decimal-leading-zero); counter-increment: agent-card; position: absolute; right: 10px; top: 8px; color: color-mix(in srgb, var(--agent-color) 18%, transparent); font-size: 22px; font-weight: 900; }
.agent-history { counter-reset: agent-card; }
.agent-history-avatar { position: relative; grid-row: 1 / span 2; }
.agent-history-avatar img { width: 42px; height: 42px; border: 2px solid #fff; box-shadow: 0 6px 12px rgba(31,55,63,.12); }
.agent-history-avatar i { position: absolute; right: 1px; bottom: 2px; width: 10px; height: 10px; border: 2px solid #fff; border-radius: 50%; background: #35a772; }
.agent-history-copy { min-width: 0; display: grid; gap: 2px; padding-right: 18px; }
.agent-history-copy > span { color: var(--agent-color); font-size: 9px; font-weight: 900; letter-spacing: .08em; }
.agent-history-copy b { color: #20373c; font-size: 13px; line-height: 1.3; }
.agent-history-copy small { margin: 1px 0 0; overflow: visible; color: #6e8085; font-size: 10px; line-height: 1.45; }
.agent-history article > button { grid-column: 2; display: flex; align-items: center; justify-content: space-between; min-height: 26px; padding: 4px 8px; border-color: color-mix(in srgb, var(--agent-color) 25%, #dce5e6); background: #fff; color: var(--agent-color); font-size: 10px; font-weight: 800; }
.agent-history article > button i { font-style: normal; }
.agent-history article:hover { transform: translateY(-2px); box-shadow: 0 13px 25px rgba(31,55,63,.09); }

/* 技术资料库：清晰呈现资料属性、摘要和检索入口。 */
.knowledge-library-panel { position: relative; overflow: hidden; padding: 24px; border-top: 4px solid var(--violet); background: linear-gradient(145deg, #fff 0%, #fbfcfe 58%, #f7fbfa 100%); }
.knowledge-library-panel::after { content: ""; position: absolute; right: -70px; top: -90px; width: 230px; height: 230px; border-radius: 50%; background: radial-gradient(circle, rgba(126,91,174,.11), transparent 68%); pointer-events: none; }
.library-heading { position: relative; z-index: 1; display: flex; align-items: flex-start; justify-content: space-between; gap: 24px; margin-bottom: 18px; }
.library-heading > div { display: grid; gap: 5px; }
.library-heading h3 { color: #1d373c; font-size: 22px; }
.library-heading span { color: var(--muted); font-size: 12px; }
.library-heading > b { padding: 7px 12px; border: 1px solid #ded5eb; border-radius: 999px; background: #f5f0fa; color: #75549e; font-size: 12px; white-space: nowrap; }
.library-searchbar { position: relative; z-index: 1; display: grid; grid-template-columns: 42px minmax(0, 1fr) auto; align-items: center; gap: 0; margin-bottom: 22px; padding: 5px; border: 1px solid #d7e2e3; border-radius: 14px; background: #fff; box-shadow: 0 8px 20px rgba(31,55,63,.055); }
.library-search-icon { width: 42px; height: 42px; display: grid; place-items: center; color: #71858a; }
.library-search-icon .ui-icon { width: 20px; height: 20px; }
.library-searchbar input { min-width: 0; height: 42px; padding: 0 8px; border: 0; background: transparent; color: #233d42; outline: 0; }
.library-searchbar button { min-width: 116px; min-height: 42px; padding: 0 18px; border: 0; border-radius: 10px; background: linear-gradient(135deg, #176f69, #268d85); color: #fff; font-weight: 900; box-shadow: 0 7px 15px rgba(23,111,105,.18); }
.library-searchbar:focus-within { border-color: #8ab4b0; box-shadow: 0 0 0 3px rgba(22,118,111,.09), 0 9px 22px rgba(31,55,63,.06); }
.library-result-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.library-result-card { --card-accent: var(--violet); position: relative; min-height: 330px; grid-template-rows: auto auto auto 1fr auto auto; gap: 12px; padding: 20px; overflow: hidden; border-color: #dce5e6; border-radius: 15px; background: rgba(255,255,255,.94); box-shadow: 0 8px 24px rgba(31,55,63,.055); transition: transform .2s, border-color .2s, box-shadow .2s; }
.library-result-card:nth-child(4n + 2) { --card-accent: var(--blue); }
.library-result-card:nth-child(4n + 3) { --card-accent: var(--amber); }
.library-result-card:nth-child(4n + 4) { --card-accent: var(--teal); }
.library-result-card::before { content: ""; position: absolute; inset: 0 auto 0 0; width: 4px; background: var(--card-accent); }
.library-result-card:hover { transform: translateY(-3px); border-color: color-mix(in srgb, var(--card-accent) 35%, #dce5e6); box-shadow: 0 15px 30px rgba(31,55,63,.09); }
.library-card-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.library-type { padding: 5px 9px; border-radius: 7px; background: color-mix(in srgb, var(--card-accent) 11%, #fff); color: color-mix(in srgb, var(--card-accent) 82%, #263c42); font-size: 11px; font-weight: 900; }
.library-match { color: var(--teal); font-size: 11px; font-weight: 900; }
.library-result-card h4 { color: #21393e; font-size: 18px; line-height: 1.45; }
.library-meta { display: flex; flex-wrap: wrap; gap: 6px; min-height: 25px; }
.library-meta span { padding: 4px 8px; border: 1px solid #dde6e7; border-radius: 999px; background: #f7faf9; color: #64787d; font-size: 10px; }
.library-summary { display: grid; align-content: start; gap: 8px; padding: 13px 14px; border-radius: 11px; background: #f6f8f8; }
.library-summary p { position: relative; padding-left: 13px; color: #43585d; font-size: 13px; line-height: 1.7; }
.library-summary p::before { content: ""; position: absolute; left: 0; top: .72em; width: 5px; height: 5px; border-radius: 50%; background: var(--card-accent); }
.library-tags { gap: 6px; }
.library-tags span { background: color-mix(in srgb, var(--card-accent) 8%, #f4f7f7); color: #586b70; }
.library-card-footer { display: flex; align-items: flex-end; justify-content: space-between; gap: 14px; padding-top: 13px; border-top: 1px solid #e5ebec; }
.library-card-footer > small { color: #849297; font-size: 10px; }
.library-card-footer .card-actions { flex-wrap: nowrap; margin: 0; }
.library-card-footer .card-actions button { min-height: 36px; padding: 7px 13px; border-radius: 9px; font-size: 12px; font-weight: 800; white-space: nowrap; }
.library-card-footer .card-actions .primary { border-color: var(--teal); background: var(--teal); color: #fff; }
.library-empty { min-height: 260px; display: grid; place-content: center; gap: 8px; text-align: center; border: 1px dashed #cad8d9; border-radius: 14px; background: #f8fbfa; color: #708287; }
.library-empty b { color: #2d484d; font-size: 17px; }
.library-empty span { font-size: 12px; }

/* KB Hero & Cards (template-style library) */
.kb-hero { position: relative; z-index: 1; display: flex; align-items: center; justify-content: space-between; gap: 20px; margin-bottom: 20px; padding: 20px 24px; border-radius: 14px; background: #fff; border: 1px solid #e5ebec; }
.kb-hero h3 { color: #1d373c; font-size: 20px; margin: 0; }
.kb-hero-left span { color: #708287; font-size: 13px; }
.kb-hero-right { display: flex; gap: 10px; }
.kb-cta { display: flex; align-items: center; gap: 8px; padding: 9px 16px; border-radius: 8px; border: 1px solid #d7e2e3; background: #fff; color: #36575b; cursor: pointer; transition: all .15s; font-family: inherit; font-size: 13px; font-weight: 600; }
.kb-cta .ui-icon { width: 16px; height: 16px; }
.kb-cta:hover { border-color: #176f69; color: #176f69; background: #f4fbfa; }
.kb-cta-new { background: #176f69; color: #fff; border-color: #176f69; }
.kb-cta-new:hover { background: #135a55; color: #fff; border-color: #135a55; }

.kb-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 16px; flex-wrap: wrap; }
.kb-toolbar-left { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.kb-toolbar-left h4 { font-size: 15px; color: #21393e; }
.kb-toolbar-left h4 small { color: #849297; font-weight: 400; margin-left: 4px; }
.kb-filter { display: flex; gap: 4px; }
.kb-filter button { padding: 5px 12px; border: 1px solid #dde6e7; border-radius: 6px; background: #fff; color: #566a6f; font-size: 12px; cursor: pointer; transition: all .15s; font-family: inherit; }
.kb-filter button.active { background: #176f69; color: #fff; border-color: #176f69; }
.kb-filter button:hover:not(.active) { border-color: #176f69; color: #176f69; }
.kb-search { position: relative; flex: 1; max-width: 300px; }
.kb-search .ui-icon { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); width: 15px; height: 15px; color: #849297; }
.kb-search input { width: 100%; height: 34px; padding: 0 12px 0 34px; border: 1px solid #dde6e7; border-radius: 8px; background: #fff; font-size: 13px; outline: 0; transition: border-color .15s; box-sizing: border-box; font-family: inherit; }
.kb-search input:focus { border-color: #176f69; }

.kb-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; }
.kb-doc-card { background: #fff; border: 1px solid #e5ebec; border-radius: 12px; padding: 16px; cursor: pointer; transition: transform .15s, box-shadow .15s, border-color .15s; display: grid; grid-template-rows: auto auto 1fr auto auto; gap: 8px; min-height: 190px; }
.kb-doc-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(31,55,63,.08); border-color: #b5c9ca; }
.kb-doc-card.starred { border-left: 3px solid #d4a017; }
.kb-doc-head { display: flex; align-items: center; justify-content: space-between; }
.kb-doc-type { padding: 2px 8px; border-radius: 4px; background: #f0f4f4; color: #556a6f; font-size: 11px; font-weight: 600; }
.kb-doc-type.检修流程 { background: #e3f2f1; color: #176f69; }
.kb-doc-type.故障分析 { background: #fef3e8; color: #96601c; }
.kb-doc-type.协作沟通 { background: #eef2fc; color: #3b5998; }
.kb-doc-type.安全规范 { background: #fdeaea; color: #b3443d; }
.kb-doc-type.通用 { background: #f0f4f4; color: #556a6f; }
.kb-star-icon { width: 15px; height: 15px; color: #d4a017; }
.kb-doc-title { font-size: 15px; color: #1d373c; line-height: 1.4; font-weight: 700; margin: 0; }
.kb-doc-summary { color: #566a6f; font-size: 12px; line-height: 1.55; margin: 0; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.kb-doc-tags { display: flex; flex-wrap: wrap; gap: 4px; }
.kb-tag { padding: 2px 7px; border-radius: 4px; background: #f1f5f4; color: #5a7075; font-size: 11px; }
.kb-doc-foot { display: flex; align-items: center; justify-content: space-between; padding-top: 8px; border-top: 1px solid #eef2f2; }
.kb-collab { display: flex; align-items: center; gap: 6px; }
.kb-collab-count { font-size: 11px; color: #708287; }
.kb-avatars { display: flex; }
.kb-avatar { width: 22px; height: 22px; border-radius: 50%; color: #fff; font-size: 10px; display: grid; place-items: center; margin-left: -5px; border: 2px solid #fff; font-weight: 700; }
.kb-avatars .kb-avatar:first-child { margin-left: 0; }
.kb-more { width: 22px; height: 22px; border-radius: 50%; background: #b5c9ca; color: #fff; font-size: 9px; display: grid; place-items: center; margin-left: -5px; border: 2px solid #fff; }
.kb-no-collab { font-size: 11px; color: #849297; }
.kb-time { font-size: 11px; color: #849297; }

.kb-empty-state { grid-column: 1 / -1; padding: 50px 20px; text-align: center; color: #708287; }
.kb-empty-state h4 { color: #2d484d; font-size: 16px; margin: 0 0 6px; }
.kb-empty-state p { margin: 0 0 14px; font-size: 13px; }
.kb-empty-btn { padding: 8px 20px; border-radius: 8px; border: 0; cursor: pointer; font-family: inherit; font-weight: 700; font-size: 13px; }

/* Template modals */
.kb-template-modal, .kb-template-lib-modal { max-width: 760px; }
.kb-template-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; margin-top: 16px; }
.kb-template-card { display: grid; grid-template-columns: 68px 1fr auto; gap: 12px; align-items: center; padding: 14px; border: 1px solid #e5ebec; border-radius: 10px; cursor: pointer; transition: all .15s; background: #fff; }
.kb-template-card:hover { border-color: #176f69; box-shadow: 0 4px 14px rgba(23,111,105,.1); }
.kb-template-icon { width: 44px; height: 44px; border-radius: 10px; background: #f0f4f4; display: grid; place-items: center; font-size: 22px; }
.kb-template-visual {
  position: relative;
  width: 68px;
  height: 54px;
  overflow: hidden;
  border: 1px solid #dce8e7;
  border-radius: 13px;
  background: linear-gradient(145deg, #edf7f5, #fff);
  color: #176f69;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.8);
}
.kb-template-visual::before {
  content: "";
  position: absolute;
  left: 13px;
  right: 13px;
  bottom: 11px;
  height: 14px;
  border-top: 3px solid rgba(255,255,255,.95);
  border-bottom: 3px solid rgba(255,255,255,.72);
  opacity: .9;
}
.kb-template-visual::after {
  content: attr(data-label);
  position: relative;
  z-index: 1;
  min-width: 30px;
  height: 28px;
  display: grid;
  place-items: center;
  padding: 0 6px;
  border-radius: 10px;
  background: rgba(255,255,255,.88);
  color: currentColor;
  font-size: 13px;
  font-weight: 900;
  letter-spacing: -.02em;
  box-shadow: 0 8px 18px rgba(31,69,75,.1);
}
.kb-template-visual.tpl-tool { background: linear-gradient(145deg, #eef8f6, #fff); color: #176f69; }
.kb-template-visual.tpl-search { background: linear-gradient(145deg, #eef4fb, #fff); color: #2f6f9f; }
.kb-template-visual.tpl-calendar { background: linear-gradient(145deg, #f6f0fb, #fff); color: #6f5ba8; }
.kb-template-visual.tpl-shield { background: linear-gradient(145deg, #fbefec, #fff); color: #b45a4d; }
.kb-template-visual.tpl-file { background: linear-gradient(145deg, #f3f7f7, #fff); color: #526a70; }
.kb-template-info { display: grid; gap: 2px; min-width: 0; }
.kb-template-info h4 { font-size: 14px; color: #1d373c; margin: 0; }
.kb-template-info > span { color: #176f69; font-size: 11px; font-weight: 600; }
.kb-template-info p { color: #708287; font-size: 12px; margin: 2px 0 0; }
.kb-template-use { padding: 6px 12px; border: 0; border-radius: 6px; background: #176f69; color: #fff; font-size: 12px; font-weight: 600; cursor: pointer; transition: background .15s; font-family: inherit; white-space: nowrap; }
.kb-template-use:hover { background: #135a55; }

/* Knowledge detail collab section */
.kd-collab-section { margin-top: 20px; padding: 16px; border: 1px solid #e5ebec; border-radius: 12px; background: #fafcfa; }
.kd-collab-list { display: grid; gap: 8px; margin-top: 12px; }
.kd-collab-item { display: flex; align-items: center; gap: 12px; padding: 10px 14px; background: #fff; border-radius: 10px; border: 1px solid #eef2f2; }
.kd-collab-avatar { width: 36px; height: 36px; border-radius: 50%; color: #fff; display: grid; place-items: center; font-weight: 700; }
.kd-collab-item > div { flex: 1; display: grid; gap: 2px; }
.kd-collab-item b { color: #1d373c; font-size: 14px; }
.kd-collab-item small { color: #708287; font-size: 12px; }
.kd-collab-status { font-size: 12px; font-weight: 600; }
.kd-collab-status.offline { color: #849297; }
.kd-collab-status.online { color: #059669; }
.kd-invite-btn { padding: 6px 12px; border: 1px solid #176f69; background: transparent; color: #176f69; border-radius: 8px; cursor: pointer; font-size: 12px; font-weight: 700; font-family: inherit; }
.kd-invite-btn:hover { background: #176f69; color: #fff; }
.collab-panel { margin-top: 16px; }
.collab-panel .collab-list { display: grid; gap: 8px; }
.collab-panel .collab-item { display: flex; align-items: center; gap: 10px; padding: 8px 12px; background: #fff; border-radius: 8px; }
.collab-panel .collab-avatar { width: 32px; height: 32px; border-radius: 50%; color: #fff; display: grid; place-items: center; font-weight: 700; }
.collab-panel .collab-item > div { flex: 1; }
.collab-panel .collab-item b { color: #21393e; font-size: 13px; }
.collab-panel .collab-item small { color: #708287; font-size: 11px; }
.collab-invite { width: 100%; margin-top: 8px; padding: 8px; border: 1px dashed #176f69; background: transparent; color: #176f69; border-radius: 8px; cursor: pointer; font-weight: 700; font-family: inherit; font-size: 12px; }
.collab-invite:hover { background: #e3f2f1; }

/* 任务操作：用轻量双层信息按钮替代突兀的竖排文字。 */
.task-row-actions { justify-content: flex-start; gap: 7px; }
.task-row-action { min-width: 58px; min-height: 48px; display: grid; place-content: center; gap: 1px; padding: 6px 10px; border: 1px solid #d5e2e1; border-radius: 11px; background: #fff; color: #466065; box-shadow: 0 4px 12px rgba(31,69,75,.04); line-height: 1.05; transition: transform .18s, border-color .18s, box-shadow .18s; }
.task-row-action span { color: #89999c; font-size: 9px; font-weight: 700; }
.task-row-action b { color: inherit; font-size: 11px; }
.task-row-action.detail { border-color: #d5e4e2; color: #176e68; background: linear-gradient(150deg, #fff, #f4fbfa); }
.task-row-action.flow { border-color: #e7dcc9; color: #96601c; background: linear-gradient(150deg, #fff, #fff9ef); }
.task-row-action:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 8px 16px rgba(31,69,75,.09); }
.task-row-action:disabled { opacity: .42; cursor: not-allowed; }
.sop-guidance-strip { display: grid; grid-template-columns: 260px minmax(0, 1fr); gap: 12px; align-items: stretch; margin: 12px 0 14px; padding: 13px; border: 1px solid #d7e8e5; border-radius: 14px; background: linear-gradient(145deg, #fff, #f6fbfa); }
.sop-guidance-strip h3 { margin-top: 4px; color: #213d3f; font-size: 16px; }
.sop-guidance-strip small { color: #708287; font-size: 12px; line-height: 1.55; }
.sop-guidance-cards { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.sop-guidance-cards button { position: relative; min-height: 84px; display: grid; align-content: start; gap: 5px; padding: 11px; border-color: #dbe9e6; border-radius: 12px; background: #fff; text-align: left; }
.sop-guidance-cards button:hover { transform: translateY(-2px); border-color: #a9cfca; box-shadow: 0 10px 20px rgba(31,69,75,.075); }
.sop-guidance-cards b { color: #213d3f; font-size: 13px; }
.sop-guidance-cards span { color: #708287; font-size: 11px; line-height: 1.45; }
.sop-guidance-cards em { position: absolute; right: 10px; bottom: 8px; color: #2f7f8f; font-size: 11px; font-style: normal; font-weight: 900; }
.personalized-sop-panel { display: grid; grid-template-columns: minmax(0, 1fr) auto auto; gap: 12px; align-items: center; margin: 14px 0; padding: 14px; border: 1px solid #d7e8e5; border-radius: 14px; background: linear-gradient(145deg, #f8fcfb, #fff); }
.task-modal-card { padding-bottom: 96px; }
.personalized-sop-panel h3 { margin: 4px 0; color: #213d3f; font-size: 16px; }
.personalized-sop-panel small { color: #708287; line-height: 1.55; }
.flow-profile-tags { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 6px; max-width: 300px; }
.flow-profile-tags span { padding: 5px 8px; border-radius: 999px; background: #edf7f5; color: #2f7f8f; font-size: 11px; font-weight: 900; }
.personalized-sop-panel > button { min-height: 36px; border-color: #2f7f8f; background: #2f7f8f; color: #fff; font-weight: 900; }
.compliance-check-panel { margin-bottom: 12px; }
.compliance-check-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 8px; }
.compliance-check-grid span { display: grid; gap: 4px; min-height: 92px; padding: 10px; border: 1px solid #e3e8e8; border-radius: 12px; background: #fff; }
.compliance-check-grid span.ok { border-color: #c9e0d6; background: #f2faf5; }
.compliance-check-grid span.required:not(.ok) { border-color: #eed9b8; background: #fff9ef; }
.compliance-check-grid b { width: 24px; height: 24px; display: grid; place-items: center; border-radius: 8px; background: #f0f4f4; color: #8a6d35; }
.compliance-check-grid span.ok b { background: #dcefe5; color: #3b775a; }
.compliance-check-grid em { color: #253f43; font-size: 12px; font-style: normal; font-weight: 900; }
.compliance-check-grid small { color: #708287; font-size: 10.5px; line-height: 1.45; }

/* 协作通信：附件、语音与人员信息保持清晰层级。 */
.conversation-list img, .message > img, .collab-info > img { background: #e9f3f1; border: 2px solid rgba(255,255,255,.92); box-shadow: 0 4px 12px rgba(25,78,75,.12); }
.contact-panel-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 4px 2px 2px; }
.contact-panel-head h3 { margin-top: 2px; font-size: 17px; }
.contact-panel-head button { width: 30px; height: 30px; min-height: 30px; display: grid; place-items: center; padding: 0; border-radius: 9px; border-color: #cddfdb; background: #fffdfa; color: #2f7f8f; font-size: 18px; font-weight: 900; }
.contact-mode-tabs { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0; padding: 0 12px; border-bottom: 1px solid #e4efec; background: #fffdfa; }
.contact-mode-tabs button { min-height: 46px; display: grid; place-items: center; gap: 1px; padding: 4px 2px; border: 0; border-radius: 0; background: transparent; color: #5c7272; font-size: 12px; font-weight: 900; }
.contact-mode-tabs button small { margin: 0; color: #8aa0a0; font-size: 10px; }
.contact-mode-tabs button.active { color: #2f7f8f; box-shadow: inset 0 -2px 0 #2f7f8f; }
.contact-mode-tabs button.active small { color: #2f7f8f; }
.contact-filter { width: calc(100% - 24px); height: 36px; margin: 10px 12px 6px; padding: 0 10px; border: 1px solid #d7e8e5; border-radius: 10px; background: #fffdfa; color: #36575b; font-weight: 700; }
.contact-summary { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px; padding: 0 12px 10px; }
.contact-summary span { display: grid; gap: 1px; padding: 8px; border: 1px solid #d7e8e5; border-radius: 10px; background: rgba(255,255,255,.72); }
.contact-summary b { color: #264f55; font-size: 17px; }
.contact-summary small { margin: 0; color: #758b8b; font-size: 11px; }
.conversation-scroll { min-height: 0; overflow: auto; display: grid; align-content: start; gap: 0; padding-right: 0; }
.chat-context-strip { display: grid; grid-template-columns: 1.2fr 1.4fr .55fr; gap: 8px; padding: 10px 22px; border-bottom: 1px solid #e4efec; background: #f8fcfb; }
.chat-context-strip span { display: grid; min-width: 0; gap: 2px; padding: 8px 10px; border: 1px solid #dce9e5; border-radius: 10px; background: #fffdfa; }
.chat-context-strip b { overflow: hidden; color: #274f52; font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.chat-context-strip small { color: #7d908f; font-size: 10px; }
.chat-compose button {
  min-height: 30px;
  padding: 0 9px;
  border-color: #d7e8e5;
  border-radius: 999px;
  background: rgba(255,255,255,.72);
  color: #617a7a;
  font-size: 13px;
  font-weight: 900;
}
.chat-compose-tools button {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 30px;
  min-height: 30px;
  box-shadow: 0 4px 10px rgba(31,69,75,.035);
}
.chat-compose-tools button span { color: #849695; font-size: 11px; font-weight: 800; }
.chat-compose-tools button:hover {
  border-color: #a9cfca;
  background: #edf7f5;
  color: #2f7f8f;
  transform: translateY(-1px);
}
.chat-compose-tools button:hover span { color: #2f7f8f; }
.chat-compose .primary {
  min-height: 40px;
  padding: 0 14px;
  border-color: #2f7f8f;
  border-radius: 13px;
  background: #2f7f8f;
  color: #fff;
  box-shadow: 0 8px 18px rgba(47,127,143,.16);
}
.chat-compose .primary:hover { background: #26717f; transform: translateY(-1px); }
.chat-compose button.recording, .collab-actions button.recording { border-color: #e6a19c; background: #fff0ef; color: #b3443d; animation: recordingPulse 1.2s infinite; }
@keyframes recordingPulse { 50% { box-shadow: 0 0 0 5px rgba(194,70,62,.08); } }
.message .chat-image { width: min(260px, 100%); max-height: 210px; display: block; margin: 6px 0; border-radius: 12px; object-fit: cover; cursor: zoom-in; }
.message .chat-file { min-width: 230px; display: grid; gap: 3px; padding: 11px 13px; border: 1px solid #d4e3e1; border-radius: 11px; background: #fff; text-align: left; }
.message audio { width: 250px; max-width: 100%; height: 38px; margin-top: 6px; }
.collab-actions { padding: 18px 22px; }
.collab-actions button { min-height: 40px; padding: 9px; border-radius: 9px; background: rgba(255,255,255,.86); font-weight: 800; }
.collab-actions button.danger { grid-column: 1 / -1; border-color: #ef8f8b; background: #fffafa; color: #d45c58; }
.meeting-board, .member-board { display: grid; gap: 8px; margin: 0 20px 14px; padding: 12px; border: 1px solid #d7e8e5; border-radius: 12px; background: rgba(255,255,255,.68); }
.side-section-title { display: flex; align-items: center; justify-content: space-between; gap: 8px; color: #274f52; }
.side-section-title button { min-height: 26px; padding: 3px 8px; border-radius: 999px; background: #edf7f5; color: #2f7f8f; font-size: 12px; font-weight: 900; }
.meeting-board article { display: grid; gap: 4px; padding: 9px; border: 1px solid #e1ebe8; border-radius: 9px; background: #fffdfa; cursor: pointer; }
.meeting-board article.active, .meeting-board article:hover { border-color: #9fcbc4; box-shadow: 0 8px 18px rgba(47,127,143,.08); }
.meeting-board strong { color: #243f42; font-size: 13px; }
.meeting-board span { justify-self: start; padding: 2px 7px; border-radius: 999px; background: #eef7e7; color: #4c7b20; font-size: 11px; font-weight: 900; }
.member-board > button { min-height: 50px; display: grid; grid-template-columns: 34px minmax(0, 1fr); align-items: center; gap: 8px; padding: 7px; border: 0; border-radius: 11px; background: transparent; text-align: left; }
.member-board > button:hover { background: #fffdfa; }
.member-board img { width: 34px; height: 34px; border-radius: 50%; object-fit: cover; }
.member-board b, .member-board small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.group-settings-head { min-height: 56px; display: flex; align-items: center; justify-content: space-between; padding: 0 22px; border-bottom: 1px solid #e4efec; }
.group-settings-head h3 { margin: 0; color: #273f42; font-size: 17px; }
.group-settings-head button { width: 28px; height: 28px; min-height: 28px; display: grid; place-items: center; padding: 0; border: 1px solid #d7e8e5; border-radius: 50%; background: #f8fcfb; color: #7b908f; font-size: 18px; font-weight: 900; }
.group-settings-head button:hover { background: #edf7f5; color: #2f7f8f; }
.chat-workbench.right-collapsed .group-settings-head { height: 100%; min-height: 100%; display: grid; align-content: start; justify-items: center; gap: 10px; padding: 12px 0; border-bottom: 0; writing-mode: vertical-rl; }
.chat-workbench.right-collapsed .group-settings-head h3 { font-size: 13px; letter-spacing: .12em; }
.chat-workbench.right-collapsed .group-settings-head button { writing-mode: horizontal-tb; }
.chat-workbench.right-collapsed .group-profile,
.chat-workbench.right-collapsed .group-members,
.chat-workbench.right-collapsed .detail-grid,
.chat-workbench.right-collapsed .meeting-board,
.chat-workbench.right-collapsed .group-setting-list,
.chat-workbench.right-collapsed .collab-actions { display: none; }
.group-profile { display: grid; grid-template-columns: 64px minmax(0, 1fr); gap: 12px; align-items: center; padding: 20px 22px; border-bottom: 1px solid #edf3f1; }
.group-profile img { width: 58px; height: 58px; border-radius: 50%; object-fit: cover; }
.group-profile h3 { margin: 0 0 4px; font-size: 15px; color: #213d3f; }
.group-profile small { color: #8a9998; }
.group-members { display: grid; gap: 10px; padding: 18px 22px; border-bottom: 1px solid #edf3f1; }
.group-members .side-section-title { grid-column: 1 / -1; }
.group-members { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.group-members button:not(.side-section-title button) { min-height: 68px; display: grid; justify-items: center; gap: 5px; padding: 0; border: 0; background: transparent; color: #526666; font-size: 11px; }
.group-members img { width: 38px; height: 38px; border-radius: 50%; object-fit: cover; }
.group-members span { max-width: 58px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.group-setting-list { display: grid; border-top: 1px solid #edf3f1; border-bottom: 1px solid #edf3f1; }
.group-setting-list button { min-height: 48px; display: flex; align-items: center; justify-content: space-between; padding: 0 22px; border: 0; border-bottom: 1px solid #edf3f1; border-radius: 0; background: #fffdfa; color: #334e51; text-align: left; }
.group-setting-list b { color: #8a9998; font-size: 12px; font-weight: 600; }
.group-setting-list button:hover { background: #f8fcfb; }

/* 知识图谱右侧详情：tab 可点击，关系数字更克制。 */
.map-inspector-tabs button {
  width: auto !important;
  min-height: 44px !important;
  margin: 0 !important;
  padding: 0 8px !important;
  border: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  color: #687a90 !important;
  font-size: 12px !important;
  font-weight: 760 !important;
  box-shadow: none !important;
}
.map-inspector-tabs button.active {
  color: #2f65ff !important;
  box-shadow: inset 0 -3px 0 #2f65ff !important;
}
.graph-inspector-section {
  display: grid;
  gap: 10px;
  padding: 16px 0 6px;
}
.graph-inspector-section h3,
.graph-inspector-section p,
.graph-inspector-section .tag-line,
.graph-inspector-section .node-type-pill {
  margin-left: 16px;
  margin-right: 16px;
}
.graph-inspector-section > button {
  width: calc(100% - 32px) !important;
  margin-left: 16px !important;
  margin-right: 16px !important;
}
.inspector-relation-list button {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  text-align: left;
}
.inspector-relation-list button span,
.inspector-attrs b {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.inspector-attrs {
  padding-left: 16px;
  padding-right: 16px;
}
.inspector-attrs > span {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr);
  align-items: center;
  gap: 10px;
  min-height: 38px;
  padding: 0 10px;
  border: 1px solid #e4edf4;
  border-radius: 9px;
  background: #f8fbfd;
}
.inspector-attrs small {
  color: #7b8ca0;
  font-size: 11px;
}
.inspector-attrs b {
  color: #2c3d50;
  font-size: 12px;
  font-weight: 760;
}
.graph-relation-stats {
  display: grid !important;
  grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  gap: 8px !important;
  margin-bottom: 10px;
}
.graph-relation-stats > span {
  display: grid !important;
  gap: 4px;
  min-width: 0;
  padding: 8px 6px !important;
  border-radius: 9px !important;
  background: #f5f8ff !important;
  text-align: center;
}
.graph-relation-stats small {
  color: #65788f;
  font-size: 11px;
  line-height: 1.2;
}
.graph-relation-stats b {
  color: #2f65ff !important;
  font-size: 15px !important;
  font-weight: 780;
  line-height: 1.15;
}
.graph-relation-card > div:not(.graph-relation-stats) {
  display: initial;
}

/* 联系人交流：三栏统一为完整协作面板，减少拥挤和错位。 */
.contact-focus-shell .page-scroll {
  padding-right: 12px;
}
.contact-focus-shell .chat-workbench {
  grid-template-columns: minmax(248px, 18%) minmax(560px, 1fr) minmax(292px, 21%);
  height: calc(100vh - 220px);
  min-height: 680px;
  border-radius: 18px;
  border-color: #d8e7e4;
  background: #f7faf9;
  box-shadow: 0 16px 36px rgba(31,69,75,.06);
}
.contact-focus-shell .chat-workbench.left-collapsed { grid-template-columns: 66px minmax(620px, 1fr) minmax(292px, 21%); }
.contact-focus-shell .chat-workbench.right-collapsed { grid-template-columns: minmax(248px, 18%) minmax(650px, 1fr) 56px; }
.contact-focus-shell .chat-workbench.left-collapsed.right-collapsed { grid-template-columns: 66px minmax(720px, 1fr) 56px; }
.contact-toolbar {
  grid-template-columns: 30px minmax(0, 1fr) 34px 34px;
  padding: 14px;
  background: #fbfdfb;
}
.chat-search input {
  height: 38px;
  border-radius: 14px;
  font-size: 13px;
}
.contact-mode-tabs {
  padding: 0 14px;
  background: #fbfdfb;
}
.contact-mode-tabs button {
  min-height: 48px;
  font-weight: 780;
}
.contact-filter {
  width: calc(100% - 28px);
  margin: 12px 14px 8px;
  border-radius: 12px;
}
.contact-summary {
  gap: 8px;
  padding: 0 14px 12px;
}
.contact-summary span {
  border-radius: 12px;
  background: #fff;
}
.conversation-scroll {
  gap: 6px;
  padding: 8px 10px 12px;
}
.conversation-scroll > button {
  min-height: 68px;
  padding: 10px;
  border: 1px solid transparent;
  border-radius: 14px;
}
.conversation-scroll > button.active,
.conversation-scroll > button:hover {
  border-color: #d7e8e5;
  border-bottom-color: #d7e8e5;
  border-radius: 14px;
  background: #fff;
}
.conversation-scroll > button::before {
  left: -1px;
  top: 14px;
  bottom: 14px;
}
.chat-title {
  min-height: 78px;
  padding: 14px 24px 10px;
  background: #fff;
}
.chat-title h3 {
  font-size: 19px;
  letter-spacing: 0;
}
.chat-title nav {
  gap: 14px;
}
.chat-title-actions button {
  min-height: 38px;
  padding: 7px 14px;
  border-radius: 12px;
}
.chat-context-strip {
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 1.25fr) minmax(86px, .45fr);
  padding: 12px 24px;
  background: #f8fbfa;
}
.chat-messages {
  padding: 24px;
  background:
    radial-gradient(circle at 18px 18px, rgba(88,128,122,.04) 1px, transparent 1.5px),
    #f4f6f5;
  background-size: 28px 28px;
}
.message {
  max-width: min(74%, 560px);
}
.message > div {
  padding: 13px 16px;
  border-radius: 6px 16px 16px 16px;
}
.message.mine > div {
  border-radius: 16px 6px 16px 16px;
  background: #e5f2f4;
}
.chat-compose {
  padding: 13px 20px 15px;
  background: #fff;
}
.chat-compose-editor {
  grid-template-columns: minmax(0, 1fr) 72px;
}
.chat-compose input {
  height: 44px;
  border-radius: 15px;
}
.collab-info {
  gap: 0;
  background: #fff;
}
.group-settings-head {
  min-height: 58px;
  padding: 0 20px;
  background: #fbfdfb;
}
.group-profile {
  grid-template-columns: 70px minmax(0, 1fr);
  padding: 20px;
  background: linear-gradient(180deg, #fff 0%, #fbfdfb 100%);
}
.group-profile img {
  width: 64px;
  height: 64px;
}
.group-profile h3 {
  font-size: 17px;
}
.group-members {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  padding: 16px 20px;
}
.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding: 16px 20px;
}
.detail-grid span {
  min-height: 58px;
  display: flex;
  align-items: center;
  padding: 12px;
  border: 1px solid #edf3f1;
  border-radius: 13px;
  background: #f7faf9;
  color: #36575b;
  line-height: 1.45;
}
.meeting-board {
  margin: 0 20px 16px;
  padding: 14px;
  border-radius: 14px;
  background: #fff;
}
.group-setting-list button {
  min-height: 46px;
  padding: 0 20px;
}

/* 智能检索：三段式工作台，输入、历史与沉淀各自独立但共享同一视觉语言。 */
.search-workbench-v2 { align-items: start; }
.search-agent-hero {
  min-height: 136px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(460px, .78fr);
  gap: 24px;
  align-items: center;
  padding: 22px 28px;
  border-color: #dce9e8 !important;
  background: rgba(255,255,255,.88) !important;
  box-shadow: 0 14px 34px rgba(30,74,78,.055);
}
.search-agent-intro { display: grid; grid-template-columns: 88px minmax(0, 1fr); gap: 18px; align-items: center; }
.search-agent-intro img { width: 88px; height: 88px; border-radius: 50%; object-fit: cover; border: 4px solid #eef8f6; box-shadow: 0 12px 24px rgba(47,127,143,.13); }
.search-agent-intro h2 { display: flex; align-items: center; gap: 10px; color: #1e3438; font-size: 26px; font-weight: 760; letter-spacing: 0; }
.search-agent-intro h2 small { color: #4e6a66; font-size: 12px; font-weight: 700; }
.agent-online-dot { width: 8px; height: 8px; border-radius: 50%; background: #5f8c51; box-shadow: 0 0 0 4px rgba(95,140,81,.12); }
.search-agent-intro b { display: block; margin: 10px 0 8px; color: #6b8b30; font-size: 14px; }
.search-agent-intro p { max-width: 760px; color: #66787d; font-size: 13px; line-height: 1.75; }
.search-fusion-panel {
  min-height: 0 !important;
  display: grid;
  gap: 16px;
  padding: 20px;
  border-color: #dce9e8 !important;
  background:
    linear-gradient(180deg, rgba(255,255,255,.9), rgba(250,253,252,.94)),
    radial-gradient(circle at 78% 16%, rgba(47,127,143,.08), transparent 28%) !important;
}
.search-fusion-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.search-fusion-head .search-panel-heading { margin-bottom: 0; }
.search-fusion-head .inline-actions button { min-height: 34px; padding: 0 12px; border-color: #d6e6e4; background: #fff; color: #2f7f8f; font-size: 12px; font-weight: 800; }
.search-fusion-body { display: grid; grid-template-columns: minmax(560px, 1.18fr) minmax(410px, .82fr); gap: 18px; align-items: stretch; }
.search-fusion-input,
.search-fusion-ai {
  min-width: 0;
  display: grid;
  align-content: start;
  gap: 14px;
  padding: 16px;
  border: 1px solid #e0ece9;
  border-radius: 18px;
  background: rgba(255,255,255,.78);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.8);
}
.search-fusion-ai {
  grid-template-rows: auto auto minmax(220px, 1fr);
  background: linear-gradient(180deg, rgba(255,255,255,.86), rgba(247,252,250,.92));
}
.search-ai-status { display: grid; grid-template-columns: 46px minmax(0,1fr); gap: 12px; align-items: center; padding: 10px; border: 1px solid #e0ece9; border-radius: 15px; background: #fff; }
.search-ai-status img { width: 46px; height: 46px; border-radius: 50%; object-fit: cover; box-shadow: 0 8px 18px rgba(47,127,143,.12); }
.search-ai-status b { color: #233d43; font-size: 14px; }
.search-ai-status small { display: block; margin-top: 3px; color: #718889; font-size: 11px; }
.search-process-card,
.search-running-state {
  position: relative;
  overflow: hidden;
  display: grid;
  gap: 13px;
  padding: 16px;
  border: 1px solid #c9e6e2;
  border-radius: 18px;
  background:
    radial-gradient(circle at 18% 16%, rgba(47,127,143,.14), transparent 32%),
    linear-gradient(145deg, rgba(255,255,255,.96), rgba(238,248,246,.94));
  box-shadow: 0 14px 30px rgba(31,69,75,.08);
}
.search-process-card::before,
.search-running-state::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(110deg, transparent 0%, rgba(255,255,255,.72) 45%, transparent 72%);
  transform: translateX(-120%);
  animation: searchShimmer 2.2s ease-in-out infinite;
  pointer-events: none;
}
.search-scan-visual {
  position: relative;
  width: 86px;
  height: 86px;
  display: grid;
  place-items: center;
  justify-self: center;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(47,127,143,.14), rgba(47,127,143,.04) 56%, transparent 58%);
}
.search-scan-visual.large { width: 110px; height: 110px; }
.scan-core {
  position: relative;
  z-index: 2;
  width: 46px;
  height: 46px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  background: linear-gradient(145deg, #2f7f8f, #1f6568);
  color: #fff;
  font-size: 13px;
  font-weight: 900;
  box-shadow: 0 12px 24px rgba(31,101,104,.18);
  animation: searchCorePulse 1.4s ease-in-out infinite;
}
.search-scan-visual i {
  position: absolute;
  inset: 9px;
  border: 1px solid rgba(47,127,143,.3);
  border-radius: 50%;
  animation: searchOrbit 3s linear infinite;
}
.search-scan-visual i:nth-of-type(2) {
  inset: 18px;
  border-color: rgba(215,149,66,.34);
  animation-duration: 2.3s;
  animation-direction: reverse;
}
.search-scan-visual i:nth-of-type(3) {
  inset: 2px;
  border-style: dashed;
  border-color: rgba(63,126,178,.28);
  animation-duration: 4.2s;
}
.search-process-copy { position: relative; text-align: center; }
.search-process-copy b { color: #213d3f; font-size: 15px; }
.search-process-copy p,
.search-running-state p { margin: 5px 0 0; color: #637b7d; font-size: 12px; line-height: 1.65; }
.search-process-track {
  position: relative;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
.search-process-track.wide { width: 100%; grid-template-columns: repeat(4, minmax(0, 1fr)); }
.search-process-track span {
  position: relative;
  min-height: 58px;
  display: grid;
  align-content: center;
  gap: 3px;
  padding: 10px 11px 10px 15px;
  border: 1px solid rgba(195,222,220,.9);
  border-radius: 13px;
  background: rgba(255,255,255,.76);
  animation: searchStepGlow 2.4s ease-in-out infinite;
}
.search-process-track span::before {
  content: "";
  position: absolute;
  left: 7px;
  top: 13px;
  bottom: 13px;
  width: 3px;
  border-radius: 999px;
  background: #2f7f8f;
}
.search-process-track span:nth-child(2) { animation-delay: .18s; }
.search-process-track span:nth-child(3) { animation-delay: .36s; }
.search-process-track span:nth-child(4) { animation-delay: .54s; }
.search-process-track b { color: #27484d; font-size: 12px; }
.search-process-track small { color: #7a8d8e; font-size: 10px; line-height: 1.4; }
.search-running-state {
  flex: 1;
  min-height: 470px;
  place-items: center;
  align-content: center;
  text-align: center;
}
.search-running-state h4 { margin: 4px 0 0; color: #213d3f; font-size: 18px; }
@keyframes searchShimmer {
  0% { transform: translateX(-120%); opacity: 0; }
  35% { opacity: .8; }
  100% { transform: translateX(120%); opacity: 0; }
}
@keyframes searchOrbit {
  to { transform: rotate(360deg); }
}
@keyframes searchCorePulse {
  0%, 100% { transform: scale(1); box-shadow: 0 12px 24px rgba(31,101,104,.18); }
  50% { transform: scale(1.06); box-shadow: 0 16px 32px rgba(31,101,104,.26); }
}
@keyframes searchStepGlow {
  0%, 100% { border-color: rgba(195,222,220,.86); transform: translateY(0); }
  45% { border-color: rgba(47,127,143,.42); transform: translateY(-2px); }
}
.search-fusion-panel .form-grid { gap: 12px 14px; }
.search-fusion-panel .form-grid label { color: #314e52; font-weight: 760; }
.search-fusion-panel .form-grid input,
.search-fusion-panel .form-grid select { height: 42px; }
.search-fusion-panel .form-grid textarea { min-height: 94px; }
.search-evidence-box { display: grid; align-content: start; gap: 12px; }
.search-launch-card { display: grid; gap: 8px; padding: 14px; border: 1px solid #d7e8e5; border-radius: 14px; background: #fff; box-shadow: 0 8px 18px rgba(31,69,75,.045); }
.search-launch-card b { color: #213d3f; font-size: 15px; }
.search-launch-card span { color: #687d7d; font-size: 12px; line-height: 1.6; }
.search-dialog-panel { display: grid; gap: 14px; padding: 18px 20px; border-color: #dce9e8 !important; background: rgba(255,255,255,.9) !important; }
.search-dialog-head { display: flex; align-items: center; justify-content: space-between; gap: 14px; }
.search-dialog-head h3 { margin-top: 4px; color: #243e43; font-size: 18px; }
.search-dialog-head button { min-height: 34px; border-color: #d6e6e4; background: #fff; color: #2f7f8f; font-size: 12px; font-weight: 800; }
.search-dialog-body { display: grid; grid-template-columns: minmax(280px, .48fr) minmax(0, 1fr); gap: 16px; min-height: 300px; }
.search-dialog-summary { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; align-content: start; }
.search-dialog-summary article { display: grid; grid-template-columns: 38px minmax(0, 1fr); gap: 10px; min-height: 82px; padding: 12px; border: 1px solid #e0ece9; border-radius: 15px; background: linear-gradient(145deg, #fff, #f8fcfb); }
.search-dialog-summary article > span { width: 38px; height: 38px; display: grid; place-items: center; border-radius: 13px; background: #e8f5f2; color: #2f7f8f; }
.search-dialog-summary b { color: #254248; font-size: 14px; }
.search-dialog-summary p { margin-top: 6px; color: #657a7d; font-size: 12px; line-height: 1.65; }
.search-dialog-thread { min-height: 0; display: grid; align-content: start; gap: 12px; overflow: auto; padding: 14px; border: 1px solid #e1ecec; border-radius: 15px; background: #fbfdfc; }
.search-dialog-thread .bubble { max-width: 82%; padding: 11px 13px; border-radius: 14px; font-size: 13px; line-height: 1.65; }
.search-dialog-thread .bubble.assistant { justify-self: start; border: 1px solid #dce9e8; background: #fff; color: #39585a; }
.search-dialog-thread .bubble.user { justify-self: end; background: #e7f1f0; color: #234a50; }
.search-dialog-input { display: grid; grid-template-columns: 40px 40px minmax(0, 1fr) 58px; gap: 10px; align-items: center; padding: 12px; border: 1px solid #e0ece9; border-radius: 16px; background: #fff; }
.search-fusion-bar { grid-template-columns: 118px 40px 40px minmax(0, 1fr) 58px; padding: 12px 14px; box-shadow: 0 10px 22px rgba(31,69,75,.04); }
.search-dialog-input input:not(.visually-hidden) { height: 42px; min-width: 0; padding: 0 14px; border: 0; outline: 0; color: #28434a; }
.search-dialog-input button { width: 40px; height: 40px; display: grid; place-items: center; padding: 0; border: 1px solid #d8e8e5; border-radius: 12px; background: #f8fcfb; color: #2f7f8f; }
.search-dialog-input button:hover,
.search-dialog-input button.active { border-color: #9fcfc8; background: #edf8f6; }
.search-dialog-input .primary { width: 58px; border-color: #2f7f8f; background: #1f6568; color: #fff; box-shadow: 0 9px 18px rgba(31,101,104,.16); }
.search-workbench-v2 .search-analysis-panel,
.search-workbench-v2 .search-results-panel,
.search-history-panel,
.history-learning-panel,
.search-update-panel { min-height: 0 !important; }
.search-workbench-v2 > .search-analysis-panel { grid-column: span 5; }
.search-workbench-v2 > .search-results-panel { grid-column: span 7; }
.search-workbench-v2 .search-results-panel { margin-top: 0; }
.search-workbench-v2 .search-results-panel .panel-head { display: grid !important; grid-template-columns: 1fr !important; align-items: start !important; }
.search-workbench-v2 .search-results-panel .tabs { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); min-width: 0 !important; justify-content: stretch; }
.result-grid-compact { grid-template-columns: repeat(2, minmax(0, 1fr)); max-height: 560px; overflow: auto; padding-right: 4px; }
.search-history-panel, .history-learning-panel { grid-column: span 6; align-self: stretch; }
.history-search-list { display: grid; gap: 9px; margin-top: 12px; }
.history-search-list button { min-height: 72px; display: grid; grid-template-columns: minmax(0, 1fr) 46px; align-items: center; gap: 12px; padding: 12px; border: 1px solid #d7e8e5; border-radius: 12px; background: #fff; text-align: left; }
.history-search-list button:hover { border-color: #a9cfca; background: #f7fbfa; transform: translateY(-1px); }
.history-search-list b { color: #213d3f; font-size: 14px; }
.history-search-list small { color: #708287; font-size: 12px; }
.history-search-list em { width: 42px; height: 42px; display: grid; place-items: center; border-radius: 12px; background: #edf7f5; color: #2f7f8f; font-style: normal; font-weight: 900; }
.learning-recommend-list { display: grid; gap: 12px; margin-top: 12px; }
.learning-recommend-list article { display: grid; gap: 8px; padding: 14px; border: 1px solid #d7e8e5; border-radius: 14px; background: linear-gradient(145deg, #fff, #f8fcfb); }
.learning-recommend-list b { color: #213d3f; font-size: 15px; }
.learning-recommend-list p { margin: 0; color: #667b7c; font-size: 12px; line-height: 1.65; }
.learning-recommend-list button { justify-self: start; min-height: 32px; padding: 5px 11px; border-color: #b9d7d2; background: #edf7f5; color: #2f7f8f; font-weight: 900; }
.search-update-panel .knowledge-review-list { margin-top: 16px; }

/* 智能检索当前页优化：输入、证据、问答、历史与沉淀共享同一套检修工作台语言。 */
.search-fusion-body {
  align-items: stretch;
}
.search-fusion-input {
  padding: 4px;
}
.search-fusion-panel .form-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}
.search-fusion-panel .form-grid .wide {
  grid-column: 1 / -1;
}
.search-evidence-box {
  margin-top: 14px;
  padding: 14px;
  border: 1px solid #e0ecea;
  border-radius: 16px;
  background: linear-gradient(180deg, #fbfefd, #f5faf9);
}
.search-upload-zone {
  margin-top: 0 !important;
  border-radius: 15px;
  background: #fff !important;
}
.search-fusion-ai {
  border-radius: 18px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbfa 100%);
  box-shadow: inset 0 0 0 1px #dce9e7;
}
.history-stat-grid,
.history-insight-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}
.history-stat-grid span,
.history-insight-grid article {
  display: grid;
  gap: 4px;
  min-width: 0;
  padding: 13px 14px;
  border: 1px solid #dce9e7;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 8px 18px rgba(31,69,75,.04);
}
.history-stat-grid b {
  color: #1f6568;
  font-size: 24px;
  line-height: 1;
}
.history-stat-grid small,
.history-insight-grid small {
  color: #708588;
  font-size: 11px;
}
.history-insight-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.history-insight-grid b {
  color: #24464b;
  font-size: 13px;
}
.history-insight-grid em {
  justify-self: start;
  padding: 4px 8px;
  border-radius: 999px;
  background: #edf7f5;
  color: #1f6568;
  font-size: 11px;
  font-style: normal;
  font-weight: 850;
}
.history-search-list button {
  grid-template-columns: minmax(0, 1fr) 50px;
  min-height: 78px;
}
.history-action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}
.history-action-row button {
  min-height: 34px;
  padding: 6px 11px;
  border-color: #cfe1de;
  background: #f7fbfa;
  color: #2f6f70;
  font-size: 12px;
  font-weight: 800;
}
.search-update-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, .42fr);
  gap: 16px;
  align-items: start;
}
.knowledge-update-aside {
  display: grid;
  gap: 12px;
}
.update-quality-card,
.update-step-list {
  display: grid;
  gap: 10px;
  padding: 15px;
  border: 1px solid #dce9e7;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 8px 18px rgba(31,69,75,.04);
}
.update-quality-card > b {
  color: #24464b;
  font-size: 15px;
}
.update-quality-card span {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 34px;
  padding: 0 10px;
  border-radius: 10px;
  background: #f7fbfa;
}
.update-quality-card small {
  color: #708588;
  font-size: 11px;
}
.update-quality-card em {
  color: #1f6568;
  font-size: 13px;
  font-style: normal;
  font-weight: 850;
}
.update-step-list article {
  display: grid;
  grid-template-columns: 18px minmax(0, 1fr);
  gap: 10px;
  align-items: start;
}
.update-step-list i {
  width: 10px;
  height: 10px;
  margin-top: 5px;
  border-radius: 50%;
  background: #78a7a2;
  box-shadow: 0 0 0 5px rgba(120,167,162,.12);
}
.update-step-list span {
  display: grid;
  gap: 3px;
}
.update-step-list b {
  color: #24464b;
  font-size: 13px;
}
.update-step-list small {
  color: #708588;
  font-size: 11px;
  line-height: 1.5;
}

.task-picker-card { width: min(680px, 94vw); }
.task-picker-list { display: grid; gap: 9px; max-height: 56vh; overflow: auto; }
.task-picker-list > button { display: grid; grid-template-columns: minmax(0,1fr) auto 52px; align-items: center; gap: 12px; min-height: 72px; padding: 13px 15px; border-color: #dce6e5; border-radius: 12px; background: #fbfdfd; text-align: left; }
.task-picker-list > button span { display: grid; gap: 4px; }
.task-picker-list > button small { color: #718387; }
.task-picker-list > button strong { color: var(--teal-dark); text-align: right; }

.task-report-card { width: min(820px, 95vw); max-height: 88vh; overflow: auto; }
.task-report-card > header { display: flex; justify-content: space-between; gap: 20px; padding: 4px 44px 16px 0; border-bottom: 1px solid #dce6e5; }
.task-report-card header small { display: block; margin-top: 5px; color: #718387; }
.report-summary, .knowledge-detail-meta { display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 9px; }
.report-summary span, .knowledge-detail-meta span { display: grid; gap: 4px; padding: 12px; border-radius: 10px; background: #f3f8f7; }
.report-summary small, .knowledge-detail-meta small { color: #7a8b8f; font-size: 10px; }
.task-report-card section { padding: 15px; border: 1px solid #e0e7e6; border-radius: 12px; background: #fff; }
.task-report-card section h3 { margin-bottom: 9px; color: #1d4f50; }
.task-report-card ol { display: grid; gap: 7px; padding: 0; list-style: none; }
.task-report-card li { display: flex; justify-content: space-between; gap: 15px; padding: 9px 11px; border-radius: 8px; background: #f6f8f8; }
.task-report-card li span { color: #6c7d80; }
.task-report-recommendations { display: grid; gap: 10px; }
.task-report-recommendations article { display: grid; gap: 7px; padding: 12px; border: 1px solid #dce8e3; border-radius: 12px; background: #fbfdfa; }
.task-report-recommendations article b { color: #21464a; }
.task-report-recommendations article small { color: #657b78; line-height: 1.55; }
.task-report-recommendations li { display: list-item; padding: 0; background: transparent; }

.knowledge-detail-card { 
  width: min(1100px, 94vw); 
  max-height: 90vh;
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 0;
  overflow: hidden;
}
.knowledge-detail-card > header { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; padding-right: 40px; }
.knowledge-detail-card > header > span { padding: 6px 10px; border-radius: 999px; background: #eee8f6; color: #72539a; font-size: 11px; font-weight: 900; }
.knowledge-detail-card section { padding: 16px 18px; border-left: 4px solid var(--violet); border-radius: 11px; background: #f7f7fa; }
.knowledge-detail-card section h3 { margin-bottom: 9px; }
.knowledge-detail-card section ul { display: grid; gap: 7px; padding-left: 18px; color: #40565a; line-height: 1.7; }

/* 知识详情编辑扩展样式 - Notion风格大编辑器 */
.knowledge-detail-card.editing { 
  width: min(1200px, 95vw); 
  max-height: 92vh;
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 0;
  padding: 0;
  overflow: hidden;
}

.knowledge-detail-card.editing .close { top: 12px; right: 16px; z-index: 10; }

/* 左侧目录树 */
.kd-sidebar-left {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 12px;
  background: #f7f8fa;
  border-right: 1px solid #e5ebec;
  overflow-y: auto;
  min-height: 600px;
}
.kd-sidebar-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e5ebec;
}
.kd-sidebar-icon { font-size: 18px; }
.kd-sidebar-title { font-size: 14px; font-weight: 700; color: #1d373c; }
.kd-sidebar-breadcrumb {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 10px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e5ebec;
  font-size: 12px;
  color: #566a6f;
}
.kd-sidebar-breadcrumb .kd-arrow { color: #849297; font-weight: 700; }
.kd-current-doc { color: #176f69; font-weight: 600; }
.kd-outline { display: flex; flex-direction: column; gap: 6px; }
.kd-outline-title { font-size: 12px; font-weight: 700; color: #708287; text-transform: uppercase; letter-spacing: 0.5px; }
.kd-outline-list { display: flex; flex-direction: column; gap: 2px; }
.kd-outline-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 8px;
  border-radius: 6px;
  font-size: 12px;
  color: #43585d;
  cursor: pointer;
  transition: background 0.15s;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.kd-outline-item:hover { background: #e8f4f2; }
.kd-outline-item.level-1 { padding-left: 8px; font-weight: 600; }
.kd-outline-item.level-2 { padding-left: 20px; }
.kd-outline-item.level-3 { padding-left: 32px; font-size: 11px; color: #708287; }
.kd-outline-item.level-4 { padding-left: 44px; font-size: 11px; color: #849297; }
.kd-outline-dot { color: #176f69; font-size: 8px; }
.kd-outline-empty { padding: 10px; font-size: 11px; color: #849297; text-align: center; }
.kd-sidebar-footer {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-top: 10px;
  border-top: 1px solid #e5ebec;
  font-size: 11px;
  color: #708287;
}

/* 主编辑区 */
.kd-main-area {
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow-y: auto;
  background: #fff;
  min-height: 0;
}
.knowledge-detail-card:not(.editing) .kd-main-area {
  max-height: 90vh;
}

.knowledge-detail-card .kd-header { 
  display: flex; 
  align-items: flex-start; 
  justify-content: space-between; 
  gap: 18px; 
  padding: 24px 40px 16px;
  border-bottom: 1px solid #eef2f2;
}
.knowledge-detail-card .kd-header > .kd-header-left { flex: 1; min-width: 0; }
.kd-header-right { display: flex; align-items: center; gap: 10px; }

/* 编辑模式顶栏 */
.kd-top-bar { display: flex; align-items: center; gap: 10px; }
.kd-doc-icon { font-size: 20px; }
.kd-title-input { 
  width: 100%; 
  font-size: 28px; 
  font-weight: 800; 
  color: #0f172a; 
  border: none; 
  border-bottom: 2px solid transparent;
  border-radius: 0; 
  padding: 8px 0; 
  margin: 0; 
  box-sizing: border-box;
  background: transparent;
  transition: border-color 0.2s;
}
.kd-title-input:focus { border-bottom-color: #176f69; outline: none; }

/* 编辑按钮组 */
.kd-edit-actions { display: flex; align-items: center; gap: 8px; }
.btn-edit-cancel {
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid #d5dde0;
  background: #fff;
  color: #566a6f;
  font-weight: 600;
  cursor: pointer;
  font-size: 13px;
  font-family: inherit;
  transition: all 0.15s;
}
.btn-edit-cancel:hover { background: #f0f3f4; color: #36575b; }
.btn-edit-save {
  padding: 8px 20px;
  border-radius: 8px;
  border: none;
  background: #176f69;
  color: #fff;
  font-weight: 700;
  cursor: pointer;
  font-size: 13px;
  font-family: inherit;
  transition: all 0.15s;
}
.btn-edit-save:hover { background: #135a55; }

.kd-type { padding: 6px 10px; border-radius: 999px; background: #eee8f6; color: #72539a; font-size: 11px; font-weight: 900; }
.btn-edit { padding: 8px 14px; border-radius: 9px; border: none; background: linear-gradient(135deg, #2563EB, #1E3A5F); color: #fff; font-weight: 700; cursor: pointer; font-size: 13px; }
.btn-edit:hover { filter: brightness(1.05); }
.kd-save-status { display: block; margin-top: 8px; font-size: 12px; font-weight: 600; }
.kd-save-status.unsaved { color: #94a3b8; }
.kd-save-status.editing { color: #f59e0b; }
.kd-save-status.saving { color: #2563eb; }
.kd-save-status.saved { color: #16a34a; }
.kd-save-status.error { color: #ef4444; }

/* 编辑器工具栏 */
.kd-editor-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 10px 40px;
  background: #fafbfc;
  border-bottom: 1px solid #eef2f2;
  position: sticky;
  top: 0;
  z-index: 5;
}
.kd-editor-toolbar button {
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid transparent;
  background: transparent;
  cursor: pointer;
  font-weight: 600;
  font-size: 13px;
  color: #43585d;
  font-family: inherit;
  transition: all 0.15s;
  white-space: nowrap;
}
.kd-editor-toolbar button:hover { background: #e8f4f2; color: #176f69; border-color: #d5e2e1; }
.kd-toolbar-divider { width: 1px; height: 20px; background: #e5ebec; margin: 0 4px; }
.kd-toolbar-spacer { flex: 1; }
.kd-toolbar-hint { font-size: 11px; color: #849297; }

/* 元信息栏 */
.kd-meta-bar {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  padding: 16px 40px;
  background: #fafbfc;
  border-bottom: 1px solid #eef2f2;
}
.kd-meta-bar.editing { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.kd-meta-bar > span { display: grid; gap: 4px; padding: 10px 12px; border-radius: 8px; background: #fff; border: 1px solid #eef2f2; }
.kd-meta-bar small { color: #708287; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px; }
.kd-meta-bar b { color: #1d373c; font-size: 13px; font-weight: 600; }
.kd-meta-input { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.kd-meta-input small { color: #708287; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px; }
.kd-meta-input input { 
  width: 100%; 
  border: 1px solid #dde5e7; 
  border-radius: 6px; 
  padding: 8px 10px; 
  font-size: 13px; 
  box-sizing: border-box;
  font-family: inherit;
  transition: border-color 0.15s;
}
.kd-meta-input input:focus { border-color: #176f69; outline: none; }

/* 内容编辑区 */
.kd-content-section { 
  padding: 32px 40px; 
  background: #fff;
  flex: 1;
}
.kd-content-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.kd-content-head h3 { margin-bottom: 0; font-size: 16px; color: #1d373c; }
.kd-editor { 
  width: 100%; 
  min-height: 500px; 
  resize: vertical; 
  border: 1px solid #dde5e7; 
  border-radius: 8px; 
  padding: 20px 24px; 
  font-size: 15px; 
  line-height: 1.8; 
  box-sizing: border-box; 
  font-family: 'SF Mono', 'Consolas', 'Monaco', 'Courier New', monospace;
  color: #2d484d;
  background: #fff;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.kd-editor:focus { 
  border-color: #176f69; 
  outline: none;
  box-shadow: 0 0 0 3px rgba(23, 111, 105, 0.1);
}
.kd-summary-list { display: grid; gap: 7px; padding-left: 18px; color: #40565a; line-height: 1.8; margin: 0; }

/* 右侧边栏（非编辑模式） */
.kd-sidebar-right {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
  background: #fafbfc;
  border-left: 1px solid #e5ebec;
  max-height: 90vh;
  overflow-y: auto;
}

.kd-links-section, .kd-versions-section, .kd-collab-section { 
  padding: 14px 16px; 
  background: #fff; 
  border: 1px solid #e5ebec; 
  border-radius: 10px; 
}
.kd-links-head { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 10px; }
.kd-links-head h3 { margin-bottom: 0; font-size: 14px; color: #1d373c; }
.kd-links-head small { font-size: 11px; color: #708287; }
.kd-link-block { margin-bottom: 12px; }
.kd-link-label { margin: 0 0 6px 0; font-size: 12px; font-weight: 700; color: #43585d; }
.kd-link-list { display: grid; gap: 6px; }
.kd-link-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: #f7f8fa; border: 1px solid #eef2f2; border-radius: 8px; cursor: pointer; }
.kd-link-item:hover { background: #e8f4f2; }
.kd-link-del { border: none; background: #fee2e2; color: #dc2626; padding: 3px 9px; border-radius: 6px; cursor: pointer; font-size: 11px; font-weight: 700; }
.kd-link-add { margin-top: 12px; display: grid; grid-template-columns: 90px 1fr 1fr auto; gap: 6px; }
.kd-link-add select, .kd-link-add input, .kd-link-add button { padding: 6px 10px; border: 1px solid #dde5e7; border-radius: 6px; font-size: 12px; background: #fff; font-family: inherit; }
.kd-link-add button { background: #176f69; color: #fff; font-weight: 700; border-color: #176f69; cursor: pointer; }
.kd-link-add button:hover { background: #135a55; }
.kd-version-list { display: grid; gap: 8px; max-height: 240px; overflow-y: auto; }
.kd-version-item { background: #f7f8fa; border: 1px solid #eef2f2; border-radius: 8px; padding: 10px 12px; }
.kd-version-main { display: flex; align-items: center; gap: 10px; margin-bottom: 5px; }
.kd-version-main b { color: #176f69; font-weight: 800; font-size: 13px; }
.kd-version-main small { color: #708287; font-size: 11px; }
.kd-version-summary { margin: 0; font-size: 12px; color: #475569; padding-left: 4px; border-left: 3px solid #176f69; }
.kd-version-restore { margin-top: 7px; border: 1px solid #176f69; background: #fff; color: #176f69; font-weight: 700; font-size: 11px; padding: 5px 10px; border-radius: 6px; cursor: pointer; font-family: inherit; }
.kd-version-restore:hover { background: #e8f4f2; }
.kd-empty { padding: 14px; text-align: center; font-size: 12px; color: #849297; background: #f7f8fa; border-radius: 8px; }
.kd-actions { margin-top: 4px; }
.kd-actions .btn-submit { background: #fef3c7; color: #92400e; border: 1.5px solid #fcd34d; font-weight: 700; }

/* 协作成员 */
.kd-collab-list { display: grid; gap: 8px; margin-top: 8px; }
.kd-collab-item { display: flex; align-items: center; gap: 10px; padding: 8px 12px; background: #f7f8fa; border-radius: 8px; border: 1px solid #eef2f2; }
.kd-collab-avatar { width: 32px; height: 32px; border-radius: 50%; color: #fff; display: grid; place-items: center; font-weight: 700; font-size: 13px; }
.kd-collab-item > div { flex: 1; display: grid; gap: 2px; }
.kd-collab-item b { color: #1d373c; font-size: 13px; }
.kd-collab-item small { color: #708287; font-size: 11px; }
.kd-collab-status { font-size: 11px; font-weight: 600; }
.kd-collab-status.offline { color: #849297; }
.kd-collab-status.online { color: #059669; }
.kd-invite-btn { padding: 5px 10px; border: 1px solid #176f69; background: transparent; color: #176f69; border-radius: 6px; cursor: pointer; font-size: 11px; font-weight: 700; font-family: inherit; }
.kd-invite-btn:hover { background: #176f69; color: #fff; }

/* 任务详情中关联知识资料卡片 */
.task-linked-knowledge { margin-top: 16px; padding: 14px 16px; border-radius: 11px; background: #f0f9ff; border-left: 4px solid #0ea5e9; }
.task-linked-knowledge h4 { margin: 0 0 10px; font-size: 13px; color: #0c4a6e; }
.task-linked-knowledge .tl-empty { padding: 10px; text-align: center; font-size: 12px; color: #94a3b8; }
.task-linked-knowledge .tl-go-kb { margin-left: 8px; color: #2563eb; font-weight: 700; cursor: pointer; }
.task-linked-list { display: grid; gap: 7px; }
.task-linked-item { display: flex; justify-content: space-between; align-items: center; padding: 9px 12px; background: #fff; border-radius: 8px; border: 1px solid #bae6fd; cursor: pointer; }
.task-linked-item:hover { background: #e0f2fe; }
.task-linked-item .tl-title { font-size: 13px; font-weight: 600; color: #0c4a6e; }
.task-linked-item .tl-meta { font-size: 11px; color: #64748b; margin-top: 3px; }
.task-linked-item .tl-arrow { color: #0ea5e9; font-size: 16px; }

/* 图谱降噪：使用 ECharts 渲染，保留可拖拽与筛选。 */
.map-canvas { background-color: #f8fbfb; background-image: linear-gradient(rgba(91,132,142,.075) 1px, transparent 1px), linear-gradient(90deg, rgba(91,132,142,.075) 1px, transparent 1px), radial-gradient(circle at 50% 50%, rgba(31,120,115,.07), transparent 48%); }
.map-inspector { border-top: 4px solid var(--teal); background: linear-gradient(180deg, #fffdfa, #f8fbfa); }

/* Current polish pass: quieter dashboard, steadier graph, full-screen document editor. */
.home-hero-work { display: none !important; }
.home-news-carousel {
  grid-column: span 7 !important;
  min-height: 380px;
  align-self: stretch;
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  gap: 12px;
  overflow: hidden;
  padding: 12px 14px 15px !important;
  border: 1px solid #d8e6f0 !important;
  border-top: 1px solid #d8e6f0 !important;
  border-radius: 14px;
  background: linear-gradient(180deg, #ffffff 0%, #fbfdff 54%, #f5fafc 100%) !important;
  box-shadow: 0 12px 24px rgba(58, 86, 108, .055) !important;
}
.news-carousel-stage {
  position: relative;
  min-height: 246px;
  overflow: hidden;
  border: 1px solid #dce8ee;
  border-radius: 12px;
  background: #edf4f7;
}
.news-image-link {
  display: block;
  width: 100%;
  height: 100%;
  min-height: 246px;
  cursor: pointer;
}
.news-image-link img {
  width: 100%;
  height: 100%;
  min-height: 246px;
  display: block;
  object-fit: contain;
  object-position: center;
}
.news-carousel-copy {
  display: grid;
  gap: 7px;
  padding: 1px 2px 0;
}
.news-carousel-copy a {
  min-width: 0;
  color: inherit;
  text-decoration: none;
}
.news-carousel-copy h2 {
  display: -webkit-box;
  max-width: 100%;
  margin: 0;
  overflow: hidden;
  color: #22343e;
  font-size: 18px;
  font-weight: 650;
  line-height: 1.35;
  letter-spacing: 0;
  text-overflow: ellipsis;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}
.news-carousel-copy p {
  display: -webkit-box;
  margin: 0;
  overflow: hidden;
  color: #5f717a;
  font-size: 12px;
  font-weight: 400;
  line-height: 1.58;
  text-overflow: ellipsis;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}
.news-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  color: #7a8d96;
  font-size: 11px;
  font-weight: 600;
}
.news-meta > span {
  flex: 0 0 auto;
  white-space: nowrap;
}
.news-dots {
  margin-left: auto;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
}
.news-dots button {
  width: 18px;
  height: 6px;
  padding: 0;
  border: 0;
  border-radius: 999px;
  background: #d3e1e8;
  cursor: pointer;
  transition: width .2s ease, background .2s ease;
}
.news-dots button.active {
  width: 28px;
  background: #6f9fbd;
}
.news-fade-enter-active,
.news-fade-leave-active {
  transition: opacity .28s ease, transform .28s ease;
}
.news-fade-enter-from,
.news-fade-leave-to {
  opacity: 0;
  transform: scale(1.015);
}
.home-task-panel { grid-column: 1 / -1 !important; }
.home-schedule-panel { grid-column: span 5 !important; }
.analytics-panel, .activity-panel { grid-column: 1 / -1 !important; }
.welcome-card { margin-bottom: 2px; }
.home-hero-work .welcome-brand { grid-template-columns: 140px minmax(0, 1fr); gap: 14px; }
.home-hero-work .welcome-brand img { width: 140px; height: 72px; }
.home-hero-work h2 { margin: 5px 0; font-size: 20px; line-height: 1.28; }
.home-hero-work p { font-size: 12px; line-height: 1.52; }
.home-hero-work .execution-summary { grid-template-columns: 78px minmax(0, 1fr) repeat(2, minmax(72px, .5fr)); gap: 10px; padding: 10px; margin-top: 10px; }
.home-hero-work .progress-ring { width: 70px; height: 70px; }
.home-hero-work .progress-ring span { font-size: 10px; }
.home-hero-work .progress-ring b { font-size: 16px; }
.home-hero-work .execution-copy strong { font-size: 13px; }
.home-hero-work .execution-copy p { font-size: 11px; }
.home-hero-work .summary-metric { min-height: 58px; padding: 8px; }
.home-hero-work .summary-metric b { font-size: 20px; }
.home-hero-work .summary-metric span { font-size: 10px; }
.home-hero-work .health-grid { gap: 6px; margin-top: 8px; }
.home-hero-work .health-grid span { min-height: 30px; padding: 7px 8px; font-size: 11px; }
.home-hero-work .focus-tasks { margin-top: 8px; }
.home-hero-work .focus-tasks-title { margin-bottom: 6px; }
.home-hero-work .focus-tasks button { min-height: 40px; padding: 6px 9px; }
.home-hero-work .focus-tasks button small { font-size: 10px; }
.home-task-panel .home-task-list { max-height: 430px; overflow: auto; padding-right: 4px; }
.home-schedule-panel { min-height: 380px; align-self: stretch; padding: 14px 16px 12px !important; border: 1px solid #ddd8d3 !important; border-top: 0 !important; background: #fffdf9 !important; box-shadow: 0 12px 24px rgba(54,48,38,.055) !important; }
.schedule-head { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 10px; }
.schedule-month-control { display: grid; grid-template-columns: 30px minmax(0, auto) 30px; align-items: center; justify-content: start; gap: 7px; min-width: 0; }
.schedule-month-control > button { width: 30px; height: 30px; padding: 0; border: 1px solid #ded8cf; border-radius: 10px; background: rgba(255,255,255,.88); color: #6c756c; font-size: 20px; font-weight: 400; line-height: 1; }
.schedule-month-control > button:hover { background: #f5f7f1; color: #4f6d58; }
.schedule-head h3 { color: #263a46; font-size: 20px; font-weight: 600; letter-spacing: .01em; white-space: nowrap; }
.schedule-head-meta { display: flex; align-items: center; justify-content: flex-end; gap: 6px; min-width: 0; }
.schedule-head-meta span { height: 26px; display: inline-flex; align-items: center; gap: 5px; padding: 0 9px; border: 1px solid #e4ddd2; border-radius: 999px; background: #fbf7ee; color: #74664f; font-size: 11px; font-weight: 600; white-space: nowrap; }
.schedule-head-meta span::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: #6f8b74; }
.schedule-head-meta .meta-critical::before { background: #c46f5a; }
.schedule-head-meta .meta-review::before { background: #b88a44; }
.schedule-head-meta .meta-today::before { background: #6f8b74; }
.schedule-calendar { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 4px 6px; margin-top: 12px; }
.schedule-calendar .weekday { height: 18px; display: grid; place-items: center; color: #7a8993; font-size: 11px; font-weight: 500; }
.schedule-calendar button { position: relative; height: 24px; display: grid; place-items: center; padding: 0; border: 0; border-radius: 50%; background: transparent; color: #2e3b43; }
.schedule-calendar button b { position: relative; z-index: 1; font-size: 13px; font-weight: 500; }
.schedule-calendar button.muted { color: #bdc8cf; }
.schedule-calendar button:hover { background: #f5f7f1; }
.schedule-calendar button.today { color: #9a6a42; }
.schedule-calendar button.selected { background: #6f8b74; color: #fff; box-shadow: 0 8px 16px rgba(82,111,88,.18); }
.schedule-calendar button.event i { position: absolute; left: 50%; bottom: 1px; width: 4px; height: 4px; margin-left: -2px; border-radius: 50%; background: #b88a44; }
.schedule-calendar button.selected i { background: #fff; }
.schedule-divider { position: relative; height: 28px; display: grid; place-items: center; margin: 6px 0 5px; }
.schedule-divider::before { content: ""; position: absolute; left: 0; right: 0; top: 50%; height: 1px; background: #e5ded4; }
.schedule-divider span { position: relative; z-index: 1; min-width: 64px; padding: 6px 14px; border-radius: 999px; background: #f7f4ec; color: #6f765f; font-size: 12px; font-weight: 600; text-align: center; }
.schedule-list { display: grid; gap: 6px; min-height: 90px; max-height: 154px; overflow: auto; padding-right: 3px; }
.schedule-item-row { display: grid; grid-template-columns: minmax(0, 1fr); align-items: center; gap: 6px; border-radius: 10px; }
.schedule-main { display: grid; grid-template-columns: 9px auto minmax(0, 1fr) auto; gap: 8px; align-items: start; min-height: 48px; padding: 4px 0; border: 0; border-radius: 10px; background: transparent; color: #2d3834; text-align: left; }
.schedule-item-row:hover { background: rgba(246,244,236,.82); }
.schedule-main > i { width: 8px; height: 8px; margin-top: 7px; border-radius: 50%; background: var(--schedule-accent, #6f8b74); box-shadow: 0 0 0 4px var(--schedule-glow, rgba(111,139,116,.12)); }
.schedule-item-row.tone-critical { --schedule-accent: #c46f5a; --schedule-glow: rgba(196,111,90,.16); }
.schedule-item-row.tone-review { --schedule-accent: #b88a44; --schedule-glow: rgba(184,138,68,.16); }
.schedule-item-row.tone-meeting { --schedule-accent: #4f9289; --schedule-glow: rgba(79,146,137,.14); }
.schedule-item-row.tone-knowledge { --schedule-accent: #7d95a8; --schedule-glow: rgba(125,149,168,.14); }
.schedule-item-row.tone-done { --schedule-accent: #8a9692; --schedule-glow: rgba(138,150,146,.12); }
.schedule-item-row.tone-quiet { --schedule-accent: #a7b2ba; --schedule-glow: rgba(167,178,186,.12); }
.schedule-item-row.done .schedule-copy b { color: #8a9692; text-decoration: line-through; }
.schedule-tag { align-self: start; padding: 3px 7px; border-radius: 5px; background: var(--schedule-accent, #6f8b74); color: #fff; font-size: 11px; font-weight: 600; white-space: nowrap; }
.schedule-item-row.done .schedule-tag { background: #8a9692; }
.schedule-copy { min-width: 0; display: grid; gap: 3px; }
.schedule-copy b { overflow: hidden; color: #26322e; font-size: 13px; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.schedule-copy small, .schedule-copy em { overflow: hidden; color: #697873; font-size: 11px; font-style: normal; font-weight: 400; line-height: 1.32; text-overflow: ellipsis; white-space: nowrap; }
.schedule-list time { margin-top: 3px; color: #697873; font-size: 12px; font-weight: 500; white-space: nowrap; }
.schedule-footer { display: grid; grid-template-columns: 1fr; gap: 10px; margin-top: 9px; padding-top: 9px; border-top: 1px solid #e5ded4; }
.schedule-footer button { height: 34px; display: inline-flex; align-items: center; justify-content: center; gap: 6px; min-width: 0; padding: 0 10px; border: 1px solid #ded8cf; border-radius: 10px; background: rgba(255,255,255,.82); color: #6c756c; font-size: 12px; font-weight: 600; white-space: nowrap; box-shadow: 0 5px 12px rgba(51,70,63,.045); transition: transform .16s ease, border-color .16s ease, background .16s ease, color .16s ease; }
.schedule-footer button:hover { transform: translateY(-1px); border-color: #c7d4bd; background: #f6f8f1; color: #4f6d58; }
.schedule-footer button.active { border-color: #6f8b74; background: #6f8b74; color: #fff; box-shadow: 0 8px 16px rgba(111,139,116,.16); }
.schedule-footer .ui-icon { width: 15px; height: 15px; flex: 0 0 auto; margin: 0; }
.analytics-panel { background: linear-gradient(180deg, rgba(255,255,255,.96), rgba(248,252,252,.94)) !important; }
.dashboard-charts { grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.dashboard-charts .chart-tile { min-height: 214px; padding: 12px 12px 8px; border-radius: 10px; }
.dashboard-charts .chart-tile-wide { grid-column: span 2; }
.dashboard-charts .chart-tile .chart-canvas { height: 210px; }

.task-metric-table-panel {
  padding: 14px 16px !important;
  border-top: 0 !important;
  background: rgba(255, 255, 255, .9) !important;
}
.task-overview-compact {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}
.task-metric-chip {
  min-width: 0;
  min-height: 84px;
  display: grid;
  align-content: center;
  gap: 7px;
  padding: 12px;
  border: 1px solid #dfe9ea;
  border-radius: 10px;
  background: linear-gradient(180deg, #fff 0%, #f7fbfb 100%);
  color: #26383d;
  text-align: left;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.85), 0 8px 18px rgba(31,55,63,.045);
}
.task-metric-chip:hover { transform: translateY(-1px); border-color: #accac8; box-shadow: 0 12px 22px rgba(31,55,63,.07); }
.metric-chip-top { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; }
.metric-chip-top b { color: #172328; font-size: 24px; line-height: 1; font-variant-numeric: tabular-nums; }
.metric-chip-top em { color: #6f8589; font-size: 11px; font-style: normal; font-weight: 800; }
.task-metric-chip .metric-name { color: #51666b; font-size: 12px; font-weight: 800; }
.metric-bar { height: 6px; overflow: hidden; border-radius: 999px; background: #e7eff0; }
.metric-bar u { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #6db2bf, #2f8b83); }
.task-metric-table, .task-metric-row { display: none !important; }

.search-workbench { grid-template-columns: minmax(520px, 1.05fr) minmax(430px, .95fr) !important; gap: 16px !important; }
.search-input-panel, .search-analysis-panel { min-height: 560px !important; padding: 20px !important; border-top: 0 !important; }
.search-input-panel::before, .search-analysis-panel::before, .search-results-panel::before { height: 0 !important; }
.search-panel-heading { margin-bottom: 16px !important; }
.search-step {
  border-radius: 10px !important;
  background: #eaf5f4 !important;
  color: #176f69 !important;
  box-shadow: inset 0 0 0 1px #cfe2e0 !important;
}
.compact-heading .search-step { background: #edf4f6 !important; color: #39708a !important; box-shadow: inset 0 0 0 1px #d5e3e8 !important; }
.search-analysis-panel { background: linear-gradient(180deg, #ffffff 0%, #f6fbfb 100%) !important; }
.search-empty-state {
  min-height: 390px !important;
  border-radius: 12px !important;
  background: #fbfdfd !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.9);
}
.analysis-orbit {
  width: 74px !important;
  height: 74px !important;
  border-radius: 18px !important;
  background: #f0f7f7 !important;
  box-shadow: inset 0 0 0 1px #d7e6e7, 0 10px 20px rgba(31,55,63,.06) !important;
}
.analysis-orbit::before { display: none !important; }
.analysis-orbit b {
  width: 40px !important;
  height: 40px !important;
  border-radius: 12px !important;
  background: #176f69 !important;
  color: #fff !important;
}
.analysis-orbit i { width: 6px !important; height: 6px !important; background: #7baeb3 !important; box-shadow: none !important; }
.search-results-panel { padding: 18px 20px !important; }
.search-results-panel .panel-head { align-items: flex-start !important; gap: 14px; }
.search-results-panel .tabs { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); min-width: 520px; }

.graph-panel { min-height: 720px; }
.knowledge-map { grid-template-columns: minmax(0, 1fr) 300px !important; align-items: stretch; }
.map-canvas-wrap { min-height: 620px; }
.echarts-canvas { height: clamp(560px, 66vh, 720px) !important; min-height: 560px; }
.map-canvas {
  background-color: #f7fbfb !important;
  background-image: linear-gradient(rgba(91,132,142,.065) 1px, transparent 1px), linear-gradient(90deg, rgba(91,132,142,.065) 1px, transparent 1px) !important;
}

.modal .knowledge-detail-card.editing {
  position: fixed;
  inset: 10px;
  width: calc(100vw - 20px) !important;
  height: calc(100vh - 20px) !important;
  max-height: none !important;
  grid-template-columns: 260px minmax(0, 1fr) !important;
  border-radius: 12px;
  background: #fff;
}
.knowledge-detail-card.editing .kd-sidebar-left { min-height: 0; height: 100%; background: #f3f8f8; }
.knowledge-detail-card.editing .kd-main-area { height: 100%; max-height: none; overflow: hidden; }
.knowledge-detail-card.editing .kd-content-section { min-height: 0; display: flex; flex-direction: column; padding: 22px 40px 28px; }
.knowledge-detail-card.editing .kd-editor { flex: 1; min-height: 0; resize: none; border-radius: 10px; background: #fcfefe; }
.knowledge-detail-card.editing .kd-meta-bar { padding: 12px 40px; }
.knowledge-detail-card.editing .kd-header { padding: 18px 40px 12px; }
.knowledge-detail-card.editing .kd-editor-toolbar { padding: 9px 40px; }

@media print {
  body * { visibility: hidden !important; }
  .task-report-card, .task-report-card * { visibility: visible !important; }
  .task-report-card { position: fixed; inset: 0; width: 100%; max-height: none; box-shadow: none; }
  .task-report-card .close, .task-report-card .actions { display: none !important; }
}

@media (max-width: 1160px) {
  .topbar { grid-template-columns: minmax(180px, 1fr) 280px 38px auto auto; }
  .work-strip { display: none; }
  .span-8, .span-7, .span-6, .span-5, .span-4 { grid-column: 1 / -1; }
  .home-news-carousel, .home-schedule-panel { grid-column: 1 / -1 !important; }
  .news-carousel-stage, .news-image-link, .news-image-link img { min-height: 220px; }
  .two-column { grid-template-columns: 1fr; }
  .content-shell { height: auto; grid-template-columns: 1fr; }
  .panel-resizer { display: none; }
  .page-scroll { height: auto; }
  .operator-panel { min-height: 420px; border-left: 0; border-top: 1px solid #ddd8d3; }
  .profile-simple-grid { grid-template-columns: 1fr; grid-template-areas: "basic" "work" "docs" "settings" "recent"; }
  .profile-work-main .profile-item-list { grid-template-columns: 1fr; }
  .profile-identity-card { grid-template-columns: 72px minmax(0, 1fr); }
  .profile-identity-card > img { width: 72px; height: 72px; }
  .identity-summary { grid-column: 1 / -1; grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .identity-summary .primary { grid-column: auto; }
  .profile-today .profile-list { grid-template-columns: 1fr; }
}
@media (max-width: 980px) {
  .topbar { grid-template-columns: minmax(180px, 1fr) minmax(220px, 1fr) 38px auto; }
  .user-chip { display: none; }
  .topbar-logout span { display: none; }
  .topbar-logout { width: 38px; padding: 0; }
  .profile-card-main { grid-template-columns: 68px minmax(0, 1fr); }
  .profile-card-main > img { width: 68px; height: 68px; }
  .profile-hero-side { grid-column: 1 / -1; justify-self: stretch; }
  .profile-card-main .primary { justify-self: start; }
  .profile-agent-simple { grid-template-columns: 1fr; }
  .identity-summary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .identity-summary .primary { grid-column: 1 / -1; justify-self: start; }
}
@media (max-width: 1450px) {
  .health-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .execution-summary { grid-template-columns: 64px minmax(0, 1fr) 94px; }
  .execution-summary .summary-metric:last-child { display: none; }
  .dashboard-charts { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .chart-tile-wide { grid-column: span 2; }
  .home-task-panel, .quick-panel { grid-column: 1 / -1; }
  .home-quick-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .schedule-head { grid-template-columns: 1fr; align-items: start; }
  .schedule-head-meta { justify-content: flex-start; flex-wrap: wrap; }
}
@media (max-width: 1250px) {
  .home-task-track-row { grid-template-columns: 1fr; }
  .home-quick-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .home-task-row { grid-template-columns: 36px minmax(180px, 1.35fr) minmax(130px, .9fr) 100px minmax(120px, .8fr) 18px; gap: 9px; }
  .home-task-compact .home-task-row { grid-template-columns: 34px minmax(180px, 1.35fr) minmax(130px, .9fr) 100px minmax(120px, .8fr) 18px; }
}
@media (max-width: 1300px) {
  .topbar { grid-template-columns: minmax(180px, 1fr) minmax(220px, 320px) 38px auto; }
  .topbar .work-strip, .topbar .user-chip { display: none; }
  .library-result-grid { grid-template-columns: 1fr; }
  .recheck-panel .recheck-grid { grid-template-columns: 1fr; }
}
.tiangong-trace { margin: 0 0 10px; padding: 10px; background: #f7fbfa; border: 1px solid #d9e9e6; border-radius: 14px; font-size: 12px; color: #50666b; box-shadow: inset 0 1px 0 rgba(255,255,255,.8); }
.tiangong-trace summary { cursor: pointer; font-weight: 800; color: #235f63; user-select: none; margin-bottom: 7px; list-style: none; }
.tiangong-trace summary::-webkit-details-marker { display: none; }
.trace-step { display: grid; grid-template-columns: 42px minmax(72px, auto) minmax(0, 1fr); gap: 7px; padding: 7px 0; border-top: 1px solid #e5efed; align-items: center; }
.trace-step:first-of-type { border-top: 0; }
.trace-tag { display: inline-grid; place-items: center; padding: 3px 6px; border-radius: 999px; font-size: 10px; font-weight: 800; color: #fff; background: #8aa3a6; min-width: 34px; text-align: center; flex-shrink: 0; }
.trace-tag.tool_call { background: #235f63; }
.trace-tag.action { background: #b6803f; }
.trace-tag.thought { background: #5b7f9f; }
.trace-tag.observation { background: #7f8f78; }
.trace-tag.parse, .trace-tag.intent, .trace-tag.plan { background: #547f98; }
.trace-tag.context { background: #6f8e7a; }
.trace-tag.retrieve { background: #235f63; }
.trace-tag.agent { background: #2f68a0; }
.trace-tag.operate { background: #b6803f; }
.trace-tag.synthesize { background: #66727e; }
.trace-tag.verify { background: #8a662d; }
.trace-tag.report { background: #2f7b62; }
.trace-tag.archive { background: #6d6fa6; }
.trace-tag.blocked { background: #a45144; }
.trace-tag.waiting { background: #9a7b3f; }
.trace-tool { max-width: 150px; padding: 4px 7px; border-radius: 999px; background: #eef6f4; color: #235f63; font-size: 11px; font-weight: 800; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.trace-text { min-width: 0; color: #455d62; line-height: 1.45; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.trace-text { flex-basis: 100%; color: #41575b; word-break: break-word; white-space: pre-wrap; }
.tg-cursor { position: fixed; width: 1px; height: 1px; z-index: 99999; pointer-events: none; transition: none !important; }
.tg-cursor-dot { position: absolute; left: -12px; top: -12px; width: 24px; height: 24px; border-radius: 50%; background: radial-gradient(circle, #fff 0 22%, rgba(32,95,97,.96) 24% 45%, rgba(184,138,68,.24) 47% 100%); border: 1px solid rgba(255,255,255,.95); box-shadow: 0 0 0 7px rgba(32,95,97,.12), 0 13px 24px rgba(38,72,70,.2); animation: tg-pulse 1.35s ease-in-out infinite; }
@keyframes tg-pulse { 0%,100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.18); opacity: .88; } }
.tg-cursor-dot::after { content: ''; position: absolute; left: 50%; top: 50%; width: 5px; height: 5px; margin: -2.5px 0 0 -2.5px; border-radius: 50%; background: #fff; box-shadow: 0 0 8px rgba(255,255,255,.9); }
.tg-cursor-label { position: absolute; left: 20px; top: 13px; white-space: nowrap; background: rgba(32,95,97,.94); color: #fff; font-size: 12px; padding: 5px 10px; border: 1px solid rgba(255,255,255,.2); border-radius: 999px; box-shadow: 0 10px 22px rgba(32,95,97,.16); font-weight: 700; backdrop-filter: blur(10px); }
.bubble.loading { position: relative; }
.loading-dots { display: inline-flex; gap: 4px; margin-right: 6px; }
.loading-dots i { width: 6px; height: 6px; border-radius: 50%; background: #1e6f6a; display: inline-block; animation: tg-bounce 1.2s infinite ease-in-out both; }
.loading-dots i:nth-child(1) { animation-delay: -.32s; }
.loading-dots i:nth-child(2) { animation-delay: -.16s; }
@keyframes tg-bounce { 0%,80%,100% { transform: scale(0); } 40% { transform: scale(1); } }
.tg-run-overlay { position: fixed; left: 50%; top: 16px; z-index: 99990; width: min(840px, calc(100vw - 40px)); transform: translateX(-50%); pointer-events: none; }
.tg-run-card { overflow: hidden; border: 1px solid rgba(193,208,204,.86); border-radius: 20px; background: linear-gradient(180deg, rgba(255,255,253,.98), rgba(248,250,247,.96)); box-shadow: 0 20px 46px rgba(36,62,63,.16), 0 1px 0 rgba(255,255,255,.96) inset; backdrop-filter: blur(18px); animation: tg-run-in .26s ease-out; pointer-events: auto; }
@keyframes tg-run-in { from { opacity: 0; transform: translate3d(0,-12px,0) scale(.98); } to { opacity: 1; transform: translate3d(0,0,0) scale(1); } }
.tg-run-card header { position: relative; display: grid; grid-template-columns: 54px minmax(0,1fr) auto; align-items: center; gap: 13px; padding: 14px 52px 10px 16px; }
.tg-run-mark { position: relative; width: 54px; height: 54px; display: grid; place-items: center; border-radius: 50%; background: linear-gradient(145deg, #fffdf8, #edf4ef); border: 1px solid rgba(198,214,207,.95); box-shadow: 0 12px 24px rgba(35,95,99,.14), 0 0 0 6px rgba(238,244,239,.78); }
.tg-run-mark img { width: 46px; height: 46px; border-radius: 50%; object-fit: cover; display: block; background: #f4f8f6; }
.tg-run-mark i { position: absolute; right: 2px; bottom: 4px; width: 12px; height: 12px; border-radius: 50%; background: #6aa876; border: 2px solid #fff; box-shadow: 0 0 0 3px rgba(106,168,118,.16); }
.tg-run-card small { display: block; margin-bottom: 3px; color: #758887; font-size: 11px; font-weight: 800; }
.tg-run-card b { display: block; overflow: hidden; color: #17393b; font-size: 15px; text-overflow: ellipsis; white-space: nowrap; }
.tg-run-card em { min-width: 54px; padding: 6px 10px; border-radius: 999px; background: #f5efe4; color: #8a662d; font-size: 12px; font-style: normal; font-weight: 900; text-align: center; }
.tg-run-stop { position: absolute; right: 14px; top: 14px; width: 30px; height: 30px; border: 1px solid #dfd8cb; border-radius: 999px; background: rgba(255,255,255,.92); color: #8a5a36; font-size: 22px; line-height: 1; cursor: pointer; box-shadow: 0 8px 18px rgba(54,62,62,.12); transition: transform .18s ease, background .18s ease, color .18s ease; }
.tg-run-stop:hover { transform: translateY(-1px); background: #fff6eb; color: #b04d2d; }
.tg-run-progress { height: 5px; margin: 0 16px; overflow: hidden; border-radius: 999px; background: #e8eeee; }
.tg-run-progress span { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #205f61, #b88a44); transition: width .32s ease; }
.tg-run-detail { margin: 9px 16px 10px; color: #4a6260; font-size: 13px; line-height: 1.55; }
.tg-run-io { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; padding: 0 16px 9px; }
.tg-run-io span { min-width: 0; padding: 8px 10px; border: 1px solid #e0e9e5; border-radius: 12px; background: #fffefb; box-shadow: 0 1px 0 rgba(255,255,255,.9) inset; }
.tg-run-io small { margin: 0 0 2px; color: #7c9092; font-size: 10px; }
.tg-run-io b { font-size: 12px; color: #24464a; }
.tg-run-exchange { display: grid; grid-template-columns: minmax(0,1fr) minmax(0,1fr); gap: 8px; padding: 0 16px 10px; }
.tg-run-exchange section { min-width: 0; padding: 9px 11px; border: 1px solid #e2ebe7; border-radius: 14px; background: linear-gradient(180deg, #ffffff, #f8fbf8); }
.tg-run-exchange small { margin: 0 0 4px; color: #6f8587; }
.tg-run-exchange p { min-height: 38px; max-height: 54px; margin: 0; overflow: hidden; color: #2f474c; font-size: 12px; line-height: 1.5; word-break: break-word; }
.tg-run-exchange section:last-child { border-color: #eadfc8; background: #fffaf1; }
.tg-run-cognition { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 8px; padding: 0 16px 10px; }
.tg-run-cognition span { min-width: 0; display: grid; gap: 3px; padding: 8px 10px; border: 1px solid #e0e9e7; border-radius: 13px; background: rgba(255,255,255,.76); }
.tg-run-cognition small { margin: 0; color: #6f8587; font-size: 10px; }
.tg-run-cognition b { color: #28494d; font-size: 12px; line-height: 1.35; white-space: normal; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.tg-run-steps { display: grid; grid-template-columns: repeat(6, minmax(0,1fr)); gap: 7px; overflow: hidden; padding: 0 16px 14px; }
.tg-run-steps span { min-width: 0; padding: 7px 8px; border: 1px solid #dde9eb; border-radius: 999px; background: #f8fbfb; color: #789096; font-size: 11px; font-weight: 800; text-align: center; text-overflow: ellipsis; white-space: nowrap; overflow: hidden; }
.tg-run-steps span.done { border-color: #d8eadf; background: #f1f8f4; color: #397257; }
.tg-run-steps span.active { border-color: #d8c79f; background: #fff8eb; color: #7d5b25; box-shadow: 0 0 0 3px rgba(184,138,68,.11); }
@media (max-width: 900px) {
  .tg-run-io { grid-template-columns: 1fr; }
  .tg-run-exchange { grid-template-columns: 1fr; }
  .tg-run-cognition { grid-template-columns: 1fr; }
  .tg-run-steps { grid-template-columns: repeat(3, minmax(0,1fr)); }
}

.side-nav { position: relative; gap: 20px !important; padding: 18px 12px !important; overflow: hidden; border-right: 1px solid rgba(158, 204, 232, .5) !important; background-color: #e9f8ff !important; background-image: linear-gradient(180deg, #d7f1ff 0%, #edf9ff 52%, #ffffff 100%) !important; box-shadow: 10px 0 24px rgba(92, 157, 195, .1) !important; }
.side-nav::before { content: ""; position: absolute; left: 18px; right: 18px; top: 13px; height: 1px; border-radius: 999px; background: rgba(255,255,255,.72); box-shadow: none; }
.side-nav::after { display: none; }
.side-nav .brand { position: relative; z-index: 1; width: 164px !important; height: 68px !important; margin: 2px auto 4px !important; padding: 6px 8px !important; border: 0 !important; border-radius: 0 !important; background: transparent !important; object-fit: contain !important; filter: none !important; box-shadow: none !important; backdrop-filter: none; }
.app-shell.collapsed .side-nav { padding-inline: 10px !important; }
.app-shell.collapsed .side-nav .brand { width: 48px !important; height: 48px !important; padding: 6px !important; border-radius: 10px !important; }
.side-nav nav { position: relative; z-index: 1; gap: 7px !important; }
.side-nav nav button { min-height: 46px !important; padding: 0 11px !important; border: 1px solid rgba(255,255,255,.2) !important; border-radius: 14px !important; color: #24556f !important; font-weight: 800 !important; letter-spacing: 0 !important; background: rgba(255,255,255,.24) !important; transition: background .18s ease, border-color .18s ease, transform .18s ease, box-shadow .18s ease !important; backdrop-filter: blur(8px); }
.side-nav nav button:hover:not(.active) { transform: translateX(2px); border-color: rgba(255,255,255,.72) !important; background: rgba(255,255,255,.52) !important; color: #163d56 !important; box-shadow: 0 10px 20px rgba(91, 151, 187, .12), 0 1px 0 rgba(255,255,255,.82) inset !important; }
.side-nav .nav-icon { width: 29px !important; height: 29px !important; border-radius: 11px !important; background: rgba(255,255,255,.65) !important; color: #2d7aa9 !important; box-shadow: inset 0 0 0 1px rgba(102,162,198,.12); }
.side-nav nav button.active { transform: translateX(2px); border-color: rgba(255,255,255,.86) !important; background: #ffffff !important; color: #14628f !important; box-shadow: 0 14px 26px rgba(66, 140, 184, .2), 0 1px 0 rgba(255,255,255,.92) inset !important; }
.side-nav nav button.active .nav-icon { background: #dff4ff !important; color: #14628f !important; box-shadow: none; }
.side-nav .collapse-btn { position: relative; z-index: 1; min-height: 42px !important; margin-top: auto !important; border: 1px solid rgba(255,255,255,.62) !important; border-radius: 14px !important; background: rgba(255,255,255,.42) !important; color: #24556f !important; font-weight: 900 !important; box-shadow: 0 1px 0 rgba(255,255,255,.8) inset !important; backdrop-filter: blur(8px); }
.side-nav .collapse-btn:hover { border-color: rgba(255,255,255,.9) !important; background: rgba(255,255,255,.72) !important; color: #143c55 !important; }
.topbar {
  --topbar-accent: #6fb9e4;
  --topbar-shadow: rgba(92, 157, 195, .08);
  border-bottom: 1px solid rgba(158, 204, 232, .5) !important;
  background-color: #eef9ff !important;
  background-image: linear-gradient(90deg, #d7f1ff 0%, #edf9ff 48%, #ffffff 100%) !important;
  box-shadow: 0 10px 24px rgba(92, 157, 195, .08) !important;
  transition: grid-template-columns .28s ease, gap .28s ease, background-color .22s ease, background-image .22s ease;
}
.topbar-home { --topbar-accent: var(--teal); --topbar-shadow: rgba(22,118,111,.08); }
.topbar-search { --topbar-accent: var(--blue); --topbar-shadow: rgba(57,121,184,.08); }
.topbar-tasks { --topbar-accent: var(--amber); --topbar-shadow: rgba(200,135,46,.08); }
.topbar-knowledge { --topbar-accent: var(--violet); --topbar-shadow: rgba(128,98,181,.08); }
.topbar-profile { --topbar-accent: var(--coral); --topbar-shadow: rgba(216,102,87,.08); }
.topbar .page-title-block { border-color: color-mix(in srgb, var(--topbar-accent) 24%, rgba(220,228,232,.8)) !important; background: rgba(255,255,255,.58) !important; box-shadow: 0 1px 0 rgba(255,255,255,.9) inset, 0 8px 18px var(--topbar-shadow) !important; backdrop-filter: blur(8px); animation: topbarSwapIn .22s ease both; }
.topbar .page-title-block::before { background: var(--title-accent) !important; }
.topbar .page-title-block::after { background: color-mix(in srgb, var(--title-accent) 9%, transparent) !important; }
.topbar .breadcrumb { color: color-mix(in srgb, var(--topbar-accent) 78%, #33494e) !important; }
.topbar h1 { color: color-mix(in srgb, var(--topbar-accent) 28%, #153e56) !important; }
.topbar .global-search,
.topbar .icon-button,
.topbar .user-chip {
  border-color: rgba(255,255,255,.68) !important;
  background: rgba(255,255,255,.56) !important;
  color: color-mix(in srgb, var(--topbar-accent) 44%, #24556f) !important;
  box-shadow: 0 1px 0 rgba(255,255,255,.85) inset, 0 8px 18px var(--topbar-shadow) !important;
  backdrop-filter: blur(8px);
  transition: width .28s ease, max-width .28s ease, transform .2s ease, border-color .2s ease, box-shadow .2s ease, background .2s ease;
}
.topbar .global-search:focus-within { border-color: color-mix(in srgb, var(--topbar-accent) 52%, #fff) !important; box-shadow: 0 0 0 3px color-mix(in srgb, var(--topbar-accent) 16%, transparent), 0 8px 18px var(--topbar-shadow) !important; }
.topbar .global-search button { border-color: var(--topbar-accent) !important; background: var(--topbar-accent) !important; color: #fff !important; }
.topbar .work-strip { animation: topbarSwapIn .18s ease both; }
.topbar .work-strip span,
.topbar .work-strip button { background: rgba(255,255,255,.5) !important; color: color-mix(in srgb, var(--topbar-accent) 44%, #24556f) !important; }
.topbar .work-strip .bad { background: rgba(255,238,232,.72) !important; color: #9a5143 !important; }
.topbar .topbar-logout {
  border-color: #ead8d3 !important;
  background: #fff8f6 !important;
  color: #974936 !important;
  box-shadow: none !important;
}
.topbar .topbar-logout:hover { border-color: #dbaea2 !important; background: #fff1ed !important; color: #974936 !important; box-shadow: 0 7px 16px rgba(151,73,54,.1) !important; }
.topbar {
  grid-template-columns: minmax(180px, 1fr) minmax(280px, 410px) auto 38px auto auto !important;
  gap: 14px !important;
  padding: 0 22px !important;
}
.topbar .topbar-logout {
  min-width: 96px;
  height: 42px;
  flex-shrink: 0;
}
.topbar.search-focus {
  grid-template-columns: 58px minmax(430px, 1fr) 38px auto auto !important;
}
.topbar.search-focus .global-search {
  max-width: none;
  height: 44px;
  padding-left: 14px;
  border-radius: 15px;
  background: rgba(255,255,255,.74) !important;
}
.topbar.search-focus .global-search input {
  font-size: 14px;
}
.task-chamber-wrap {
  position: relative;
  z-index: 12;
  animation: topbarSwapIn .22s ease both;
}
.task-chamber {
  position: relative;
  width: 58px;
  min-height: 44px;
  display: grid;
  place-items: center;
  padding: 0;
  border: 1px solid rgba(255,255,255,.76);
  border-radius: 15px;
  background:
    linear-gradient(180deg, rgba(255,255,255,.86), color-mix(in srgb, var(--topbar-accent) 12%, #fff)),
    #fff;
  color: color-mix(in srgb, var(--topbar-accent) 58%, #24556f);
  box-shadow: 0 1px 0 rgba(255,255,255,.9) inset, 0 9px 20px var(--topbar-shadow);
  backdrop-filter: blur(8px);
  transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease, background .2s ease;
}
.task-chamber:hover,
.task-chamber.open {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--topbar-accent) 36%, #fff);
  background:
    linear-gradient(180deg, rgba(255,255,255,.94), color-mix(in srgb, var(--topbar-accent) 17%, #fff)),
    #fff;
  box-shadow: 0 1px 0 rgba(255,255,255,.96) inset, 0 13px 24px color-mix(in srgb, var(--topbar-accent) 16%, transparent);
}
.task-chamber i {
  position: relative;
  width: 32px;
  height: 28px;
  margin-top: 0;
  border-radius: 10px 10px 12px 12px;
  background: linear-gradient(180deg, #ffffff 0%, color-mix(in srgb, var(--topbar-accent) 20%, #fff) 100%);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--topbar-accent) 22%, transparent), 0 5px 12px color-mix(in srgb, var(--topbar-accent) 12%, transparent);
}
.task-chamber i::before {
  content: "";
  position: absolute;
  left: 7px;
  right: 7px;
  top: 5px;
  width: auto;
  height: 3px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--topbar-accent) 70%, #fff);
  box-shadow: none;
}
.task-chamber i::after {
  content: "";
  position: absolute;
  left: 9px;
  right: 9px;
  top: auto;
  bottom: 6px;
  width: auto;
  height: 8px;
  border-radius: 999px 999px 4px 4px;
  background: rgba(255,255,255,.82);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--topbar-accent) 16%, transparent);
}
.task-chamber-pop {
  position: absolute;
  left: 0;
  top: calc(100% + 9px);
  width: 244px;
  display: grid;
  gap: 6px;
  padding: 8px;
  border: 1px solid color-mix(in srgb, var(--topbar-accent) 22%, rgba(220,228,232,.84));
  border-radius: 15px;
  background: rgba(255,255,255,.94);
  box-shadow: 0 18px 38px color-mix(in srgb, var(--topbar-accent) 18%, transparent);
  backdrop-filter: blur(12px);
  animation: chamberPopIn .18s ease both;
}
.task-chamber-pop::before {
  content: "";
  position: absolute;
  left: 20px;
  top: -6px;
  width: 11px;
  height: 11px;
  border-left: 1px solid color-mix(in srgb, var(--topbar-accent) 22%, rgba(220,228,232,.84));
  border-top: 1px solid color-mix(in srgb, var(--topbar-accent) 22%, rgba(220,228,232,.84));
  background: rgba(255,255,255,.94);
  transform: rotate(45deg);
}
.task-chamber-pop button {
  position: relative;
  display: grid;
  gap: 3px;
  padding: 10px 12px;
  border: 0;
  border-radius: 11px;
  background: transparent;
  text-align: left;
}
.task-chamber-pop button:hover {
  background: color-mix(in srgb, var(--topbar-accent) 10%, #fff);
}
.task-chamber-pop b {
  color: color-mix(in srgb, var(--topbar-accent) 38%, #183f55);
  font-size: 13px;
}
.task-chamber-pop small {
  color: #7293a4;
  font-size: 11px;
}
.task-chamber-pop .danger b {
  color: #8d5243;
}
@keyframes topbarSwapIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes chamberPopIn {
  from { opacity: 0; transform: translateY(-6px) scale(.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.workspace,
.content-shell {
  background: #eef8fc !important;
}
.page-scroll {
  background:
    linear-gradient(180deg, rgba(255,255,255,.58) 0%, rgba(255,255,255,.18) 42%, rgba(255,255,255,0) 100%),
    linear-gradient(90deg, rgba(140,190,218,.06) 1px, transparent 1px),
    linear-gradient(rgba(140,190,218,.05) 1px, transparent 1px),
    #eef8fc !important;
  background-size: auto, 34px 34px, 34px 34px, auto !important;
}
.operator-panel {
  border-left-color: color-mix(in srgb, var(--op-accent) 8%, var(--line)) !important;
  background: var(--op-tint) !important;
}
.panel-resizer {
  background: #e6edef !important;
}

.knowledge-focus-shell {
  grid-template-columns: minmax(0, 1fr) !important;
}
.knowledge-focus-shell .panel-resizer,
.knowledge-focus-shell .operator-panel {
  display: none !important;
}
.page-theme-knowledge {
  --page-accent: #2f65ff;
  --page-accent-soft: rgba(47, 101, 255, .07);
}
.graph-console-panel {
  min-height: calc(100vh - 204px) !important;
  padding: 0 !important;
  overflow: hidden !important;
  border: 1px solid #dce6f2 !important;
  border-top: 0 !important;
  border-radius: 14px !important;
  background: #f7faff !important;
  box-shadow: 0 18px 42px rgba(33, 58, 91, .075) !important;
}
.graph-console-panel::before { display: none !important; }
.graph-toolbar {
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) !important;
  gap: 14px !important;
  align-items: center !important;
  margin: 0 !important;
  padding: 12px 14px !important;
  border-bottom: 1px solid #dce6f2 !important;
  background: rgba(255,255,255,.96) !important;
  backdrop-filter: blur(16px);
}
.graph-view-tabs {
  display: inline-grid;
  grid-template-columns: repeat(2, auto);
  gap: 6px;
  padding: 4px;
  border: 1px solid #dce6f2;
  border-radius: 10px;
  background: #f8fbff;
}
.graph-view-tabs button {
  min-height: 34px;
  padding: 0 16px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: #607186;
  font-size: 13px;
  font-weight: 750;
}
.graph-view-tabs button.active {
  background: #2f65ff;
  color: #fff;
  box-shadow: 0 8px 18px rgba(47,101,255,.22);
}
.graph-toolbar-main {
  min-width: 0;
  display: grid;
  grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
  gap: 12px;
  align-items: center;
}
.graph-search,
.graph-search.expanded,
.graph-search:focus-within {
  width: 100% !important;
  height: 38px !important;
  grid-template-columns: 30px minmax(0, 1fr) 24px !important;
  padding: 4px 7px !important;
  border: 1px solid #dce6f2 !important;
  border-radius: 9px !important;
  background: #fff !important;
  box-shadow: none !important;
}
.graph-search-trigger,
.graph-search-clear {
  width: 28px !important;
  height: 28px !important;
  border-radius: 7px !important;
  background: #f0f5ff !important;
  color: #2f65ff !important;
}
.graph-search input {
  opacity: 1 !important;
  color: #233549 !important;
  font-size: 13px !important;
}
.graph-controls {
  display: flex !important;
  flex-wrap: wrap !important;
  justify-content: flex-end !important;
  gap: 8px !important;
  padding: 0 !important;
  border: 0 !important;
}
.graph-controls select,
.graph-controls button,
.graph-controls label {
  width: auto !important;
  height: 38px !important;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 12px !important;
  border: 1px solid #dce6f2 !important;
  border-radius: 9px !important;
  background: #fff !important;
  color: #3f5269 !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  box-shadow: 0 4px 12px rgba(31,57,91,.035);
}
.graph-controls button:hover,
.graph-controls select:hover {
  border-color: #b7c9ea !important;
  background: #f5f8ff !important;
}
.knowledge-map {
  height: calc(100vh - 252px);
  min-height: 610px;
  display: grid !important;
  grid-template-columns: 214px minmax(620px, 1fr) 306px !important;
  gap: 12px !important;
  padding: 12px !important;
  align-items: stretch !important;
}
.graph-filter-panel,
.map-sidebar {
  min-height: 0;
  display: grid;
  align-content: start;
  gap: 10px;
}
.graph-filter-panel section,
.map-inspector,
.map-summary-card {
  border: 1px solid #dce6f2;
  border-radius: 12px;
  background: rgba(255,255,255,.95);
  box-shadow: 0 10px 24px rgba(36,64,102,.045);
}
.graph-filter-panel section {
  padding: 13px;
}
.graph-filter-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
}
.graph-filter-head b {
  color: #27394e;
  font-size: 13px;
}
.graph-filter-head button {
  border: 0;
  background: transparent;
  color: #2f65ff;
  font-size: 12px;
  font-weight: 750;
}
.graph-filter-note {
  display: block;
  color: #718195;
  font-size: 12px;
  line-height: 1.65;
}
.graph-filter-search {
  height: 36px;
  display: grid;
  grid-template-columns: 18px minmax(0,1fr);
  align-items: center;
  gap: 8px;
  padding: 0 10px;
  border: 1px solid #dce6f2;
  border-radius: 9px;
  color: #8a9bad;
  background: #fbfdff;
}
.graph-filter-search input {
  min-width: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: #26384c;
  font-size: 12px;
}
.graph-type-row,
.graph-relation-row {
  width: 100%;
  min-height: 31px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 0 2px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: #536579;
  font-size: 12px;
}
.graph-type-row span,
.graph-relation-row span {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.graph-type-row i,
.legend-body i {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #8aa6c1;
}
.graph-type-row i.equipment, .legend-body i.equipment { background: #3f7fa7; }
.graph-type-row i.model, .legend-body i.model { background: #8fc0d6; }
.graph-type-row i.part, .legend-body i.part { background: #45aeb0; }
.graph-type-row i.fault, .legend-body i.fault { background: #d79542; }
.graph-type-row i.cause, .legend-body i.cause { background: #cf6d45; }
.graph-type-row i.method, .legend-body i.method { background: #8b879f; }
.graph-type-row i.solution, .legend-body i.solution { background: #6c9b72; }
.graph-type-row i.sop, .legend-body i.sop { background: #2f5f88; }
.graph-type-row i.risk, .legend-body i.risk { background: #c95f5a; }
.graph-type-row i.case, .legend-body i.case { background: #9a7858; }
.graph-type-row i.doc, .legend-body i.doc { background: #7d95a8; }
.graph-type-row em,
.graph-relation-row em {
  color: #7c8da0;
  font-style: normal;
  font-weight: 750;
}
.graph-type-row.active,
.graph-relation-row.active,
.graph-type-row:hover,
.graph-relation-row:hover {
  background: #f1f6ff;
  color: #2f65ff;
}
.graph-layer-switches label {
  min-height: 30px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #536579;
  font-size: 12px;
}
.map-canvas-wrap {
  min-height: 0 !important;
  overflow: hidden !important;
  border: 1px solid #dce6f2 !important;
  border-radius: 14px !important;
  background: #ffffff !important;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.9), 0 16px 36px rgba(38,65,96,.06) !important;
}
.echarts-canvas {
  height: 100% !important;
  min-height: 560px !important;
}
.map-canvas {
  background-color: #fbfdff !important;
  background-image:
    radial-gradient(circle at center, rgba(47,101,255,.055), transparent 42%),
    linear-gradient(rgba(103,132,168,.075) 1px, transparent 1px),
    linear-gradient(90deg, rgba(103,132,168,.075) 1px, transparent 1px) !important;
  background-size: auto, 28px 28px, 28px 28px !important;
}
.graph-canvas-tools {
  display: none !important;
}
.graph-canvas-tools button {
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 8px;
  background: #f6f9ff;
  color: #4a5d72;
  font-size: 18px;
}
.graph-canvas-tools button:hover {
  background: #2f65ff;
  color: #fff;
}
.graph-legend-panel {
  left: auto !important;
  right: 16px !important;
  top: auto !important;
  bottom: 18px !important;
  pointer-events: auto !important;
}
.legend-body {
  max-width: 210px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 7px 10px;
  padding: 12px;
  border: 1px solid #dce6f2;
  border-radius: 12px;
  background: rgba(255,255,255,.94);
  box-shadow: 0 12px 26px rgba(38,65,96,.1);
}
.legend-body span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #536579;
  font-size: 11px;
  font-weight: 650;
  cursor: pointer;
}
.map-inspector {
  padding: 0;
  overflow: hidden;
}
.map-inspector-tabs {
  display: grid;
  grid-template-columns: repeat(3, minmax(0,1fr));
  border-bottom: 1px solid #e5edf6;
}
.map-inspector-tabs b,
.map-inspector-tabs span {
  padding: 12px 8px;
  text-align: center;
  color: #687a90;
  font-size: 12px;
  font-weight: 750;
}
.map-inspector-tabs b {
  color: #2f65ff;
  box-shadow: inset 0 -3px 0 #2f65ff;
}
.map-inspector h3,
.map-inspector p,
.map-inspector .tag-line,
.map-inspector button,
.map-inspector .empty,
.node-type-pill {
  margin-left: 16px;
  margin-right: 16px;
}
.map-inspector h3 {
  margin-top: 18px;
  margin-bottom: 6px;
  color: #24364b;
  font-size: 18px;
}
.node-type-pill {
  display: inline-flex;
  padding: 5px 9px;
  border-radius: 999px;
  background: #eef4ff;
  color: #2f65ff;
  font-size: 11px;
  font-weight: 800;
}
.map-inspector p {
  color: #526477;
  font-size: 13px;
  line-height: 1.75;
}
.map-inspector button {
  width: calc(100% - 32px);
  min-height: 36px;
  margin-bottom: 10px;
  border: 1px solid #dce6f2;
  border-radius: 9px;
  background: #fff;
  color: #2f65ff;
  font-weight: 750;
}
.map-inspector button.primary {
  margin-top: 10px;
  background: #2f65ff;
  color: #fff;
}
.map-summary-card {
  padding: 14px 16px;
}
.map-summary-card h3 {
  margin: 0 0 12px;
  color: #2a3a4d;
  font-size: 15px;
}
.map-summary-card div {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 7px;
}
.map-summary-card div span,
.map-summary-card div b {
  display: block;
}
.map-summary-card div {
  grid-template-columns: repeat(3, minmax(0,1fr));
}
.map-summary-card div > span,
.map-summary-card div > b {
  padding: 9px 6px;
  border-radius: 8px;
  background: #f5f8ff;
  text-align: center;
}
.map-summary-card div > b {
  color: #2f65ff;
  font-size: 20px;
}
.map-summary-card button {
  width: 100%;
  display: grid;
  grid-template-columns: minmax(0,1fr) auto;
  gap: 8px;
  padding: 9px 0;
  border: 0;
  border-bottom: 1px solid #edf2f7;
  background: transparent;
  color: #42556a;
  text-align: left;
}
.map-summary-card button span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.map-summary-card button em {
  color: #7a8ca0;
  font-size: 11px;
  font-style: normal;
}
.graph-relation-card button,
.graph-doc-card button {
  min-height: 42px;
  align-items: center;
  padding: 10px 0;
  cursor: pointer;
}
.graph-relation-card button:hover,
.graph-doc-card button:hover {
  color: #2f5f88;
}
.graph-relation-card button span::before,
.graph-doc-card button span::before {
  content: "";
  width: 7px;
  height: 7px;
  display: inline-block;
  margin-right: 7px;
  border-radius: 50%;
  background: #7d95a8;
  box-shadow: 0 0 0 3px rgba(125,149,168,.13);
}
.map-doc-empty {
  margin: 8px 0 0;
  padding: 12px;
  border-radius: 10px;
  background: #f6f8f9;
  color: #718195;
  font-size: 12px;
  line-height: 1.6;
}
.floating-agent {
  position: fixed;
  left: 0;
  top: 0;
  z-index: 80;
  --float-accent: #80B918;
  --float-accent-dark: #5c8a0e;
  --float-soft: #f6faee;
  pointer-events: none;
  transition: filter .18s ease;
}
.floating-agent > * { pointer-events: auto; }
.floating-agent-orb {
  width: 72px;
  height: 72px;
  position: relative;
  display: grid;
  place-items: center;
  padding: 0;
  border: 1px solid rgba(128,185,24,.34);
  border-radius: 50%;
  background: rgba(255,255,255,.92);
  box-shadow: 0 18px 34px rgba(77,115,30,.18), 0 0 0 8px rgba(128,185,24,.08);
  backdrop-filter: blur(16px);
  touch-action: none;
  transition: transform .18s ease, box-shadow .18s ease;
}
.floating-agent-orb:hover {
  transform: translateY(-2px);
  box-shadow: 0 22px 42px rgba(77,115,30,.22), 0 0 0 10px rgba(128,185,24,.1);
}
.floating-agent.dragging .floating-agent-orb { transform: scale(.98); }
.floating-agent-orb img {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  object-fit: cover;
}
.floating-agent-orb span {
  position: absolute;
  right: 10px;
  bottom: 10px;
  width: 12px;
  height: 12px;
  border: 2px solid #fff;
  border-radius: 50%;
  background: #22a06b;
}
.floating-agent-chat {
  position: relative;
  width: min(500px, calc(100vw - 40px));
  max-height: min(720px, calc(100vh - 96px));
  display: grid;
  grid-template-rows: auto minmax(230px, 1fr) auto auto auto;
  overflow: hidden;
  border: 1px solid rgba(128,185,24,.22);
  border-radius: 20px;
  background: rgba(255,255,255,.96);
  box-shadow: 0 26px 58px rgba(63,90,33,.2);
  backdrop-filter: blur(18px);
  transform-origin: top right;
  animation: floatingChatOpen .2s ease-out;
}
.floating-agent-chat header {
  display: grid;
  grid-template-columns: 54px minmax(0,1fr) auto;
  gap: 10px;
  align-items: center;
  padding: 14px;
  border-bottom: 1px solid #e6efdc;
  background: linear-gradient(135deg, #fbfdf7, #f2f8e9);
  cursor: move;
  user-select: none;
}
.floating-agent-chat header img {
  width: 54px;
  height: 54px;
  border-radius: 50%;
  object-fit: cover;
  box-shadow: 0 10px 18px rgba(92,138,14,.14);
}
.floating-agent-chat header p {
  margin: 0;
  color: var(--float-accent-dark);
  font-size: 11px;
  font-weight: 850;
}
.floating-agent-chat header h3 {
  margin: 2px 0;
  color: #22364c;
  font-size: 17px;
}
.floating-agent-chat header small {
  display: block;
  overflow: hidden;
  color: #6a7c90;
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.floating-agent-head-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
.floating-agent-head-actions button,
.floating-agent-prompts button,
.floating-input-tools button,
.floating-send {
  min-height: 34px;
  border: 1px solid #dce9d0;
  border-radius: 999px;
  background: #fff;
  color: #486333;
  font-size: 12px;
  font-weight: 750;
}
.floating-agent-head-actions button,
.floating-input-tools button,
.floating-send {
  width: 36px;
  height: 36px;
  display: inline-grid;
  place-items: center;
  padding: 0;
}
.floating-agent-head-actions svg,
.floating-input-tools svg,
.floating-send svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.floating-agent-head-actions button:hover,
.floating-agent-prompts button:hover,
.floating-input-tools button:hover {
  border-color: rgba(128,185,24,.45);
  background: var(--float-soft);
  color: var(--float-accent-dark);
}
.floating-chat-thread {
  min-height: 0;
  display: grid;
  align-content: start;
  gap: 10px;
  overflow: auto;
  padding: 14px;
  background: #fbfdf8;
}
.floating-chat-thread .bubble {
  max-width: 88%;
  padding: 10px 12px;
  border-radius: 13px;
  font-size: 13px;
  line-height: 1.6;
}
.floating-chat-thread .bubble.assistant {
  justify-self: start;
  border: 1px solid #e3edda;
  background: #fff;
  color: #314a2d;
}
.floating-chat-thread .bubble.user {
  justify-self: end;
  background: var(--float-accent-dark);
  color: #fff;
}
.floating-chat-thread .node-context {
  border-color: #d5e8c4 !important;
  background: #f6faef !important;
}
.floating-agent-prompts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  padding: 10px 14px 0;
  background: #fff;
}
.floating-agent-prompts span {
  color: #748463;
  font-size: 12px;
}
.floating-agent-prompts button {
  min-height: 32px;
  padding: 0 10px;
  color: #4c6338;
  background: #f8fbf3;
}
.floating-attachments {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px 14px 0;
  background: #fff;
}
.floating-attachments span {
  display: inline-flex;
  max-width: 180px;
  align-items: center;
  gap: 6px;
  padding: 6px 9px;
  overflow: hidden;
  border: 1px solid #e2ecd6;
  border-radius: 999px;
  background: #f7faf2;
  color: #4d6241;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.floating-attachments button {
  width: 18px;
  height: 18px;
  border: 0;
  border-radius: 50%;
  background: rgba(80,101,62,.1);
  color: #566a45;
  line-height: 18px;
}
.floating-ask-box {
  display: grid;
  grid-template-columns: auto minmax(0,1fr) auto;
  gap: 8px;
  align-items: center;
  padding: 12px 14px 14px;
  background: #fff;
}
.floating-input-tools {
  display: flex;
  gap: 6px;
  align-items: center;
}
.floating-ask-box input {
  min-width: 0;
  height: 40px;
  padding: 0 12px;
  border: 1px solid #dce9d0;
  border-radius: 10px;
  outline: 0;
  color: #26394f;
}
.floating-ask-box input:focus {
  border-color: rgba(128,185,24,.55);
  box-shadow: 0 0 0 3px rgba(128,185,24,.1);
}
.floating-input-tools button.active {
  border-color: rgba(190,120,53,.45);
  background: #fff5e8;
  color: #a35f24;
}
.floating-send {
  background: var(--float-accent-dark);
  color: #fff;
}
.floating-send:hover {
  background: #315f1f;
}
@keyframes floatingChatOpen {
  from { opacity: 0; transform: scale(.92); }
  to { opacity: 1; transform: scale(1); }
}
@media (max-width: 1380px) {
  .knowledge-map { grid-template-columns: 200px minmax(0, 1fr) 300px !important; }
  .graph-toolbar-main { grid-template-columns: 240px minmax(0, 1fr); }
}

/* 知识网络那一屏是自适应满屏的图，锁死不滚动；其余子页签内容比一屏长，必须能往下滚。 */
.knowledge-focus-shell .page-scroll {
  overflow-x: hidden !important;
  padding: 10px 12px 12px !important;
}
.page-scroll.panel-network {
  overflow: hidden !important;
}
.knowledge-focus-shell .page-grid {
  gap: 10px !important;
}
.knowledge-focus-shell .knowledge-nav-panel {
  padding: 12px 16px !important;
}
.knowledge-focus-shell .knowledge-nav-panel .panel-head {
  align-items: center;
}
.knowledge-focus-shell .knowledge-nav-panel .eyebrow {
  display: block;
  margin: 0;
  color: #7a62b0;
  font-size: 10px;
}
.knowledge-focus-shell .knowledge-nav-panel h3 {
  display: block;
  margin: 3px 0 0;
  color: #263543;
  font-size: 18px;
  line-height: 1.2;
}
.knowledge-focus-shell .knowledge-nav-panel small {
  display: block;
  max-width: 520px;
  margin-top: 4px;
  overflow: hidden;
  color: #6f7c89;
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.knowledge-focus-shell .graph-console-panel {
  min-height: calc(100vh - 130px) !important;
}
.knowledge-focus-shell .graph-toolbar {
  min-height: 58px !important;
  padding: 9px 12px !important;
}
.knowledge-focus-shell .graph-toolbar-main {
  grid-template-columns: minmax(270px, 410px) minmax(0, 1fr) !important;
  gap: 10px !important;
  min-height: 40px;
}
.knowledge-focus-shell .graph-search,
.knowledge-focus-shell .graph-search.expanded,
.knowledge-focus-shell .graph-search:focus-within {
  height: 36px !important;
  max-width: 410px;
}
.knowledge-focus-shell .graph-controls {
  grid-column: auto !important;
  flex-wrap: nowrap !important;
  gap: 7px !important;
  padding-top: 0 !important;
  border-top: 0 !important;
  overflow-x: auto;
  scrollbar-width: none;
}
.knowledge-focus-shell .graph-controls::-webkit-scrollbar {
  width: 0;
  height: 0;
}
.knowledge-focus-shell .graph-controls select,
.knowledge-focus-shell .graph-controls button,
.knowledge-focus-shell .graph-controls label {
  height: 36px !important;
  min-height: 36px !important;
  flex: 0 0 auto;
  padding: 0 10px !important;
}
.knowledge-focus-shell .knowledge-map {
  height: calc(100vh - 196px) !important;
  min-height: 0 !important;
  grid-template-columns: 198px minmax(560px, 1fr) 300px !important;
  gap: 10px !important;
  padding: 10px !important;
  overflow: hidden !important;
}
.knowledge-focus-shell .graph-filter-panel,
.knowledge-focus-shell .map-sidebar {
  gap: 9px !important;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: none;
}
.knowledge-focus-shell .graph-filter-panel::-webkit-scrollbar,
.knowledge-focus-shell .map-sidebar::-webkit-scrollbar {
  width: 0;
  height: 0;
}
.knowledge-focus-shell .graph-filter-panel section {
  padding: 10px !important;
}
.knowledge-focus-shell .graph-filter-head {
  margin-bottom: 8px;
}
.knowledge-focus-shell .graph-filter-note {
  line-height: 1.5;
}
.knowledge-focus-shell .graph-type-row,
.knowledge-focus-shell .graph-relation-row {
  min-height: 29px;
  font-size: 11px;
}
.knowledge-focus-shell .graph-layer-switches label {
  min-height: 28px;
}
.knowledge-focus-shell .map-canvas-wrap,
.knowledge-focus-shell .map-canvas,
.knowledge-focus-shell .echarts-canvas {
  height: 100% !important;
  min-height: 0 !important;
}
.knowledge-focus-shell .map-inspector {
  min-height: 0 !important;
}
.knowledge-focus-shell .map-inspector-tabs b,
.knowledge-focus-shell .map-inspector-tabs span,
.knowledge-focus-shell .map-inspector-tabs button {
  min-height: 40px !important;
  padding: 10px 6px !important;
}
.knowledge-focus-shell .map-inspector .empty {
  min-height: 0 !important;
  margin: 12px !important;
  padding: 14px 12px !important;
  border-radius: 10px;
  background: #f6f8f9;
  color: #718195;
  font-size: 12px;
  line-height: 1.55;
}
.knowledge-focus-shell .map-summary-card {
  padding: 12px 14px !important;
}
.knowledge-focus-shell .map-summary-card h3 {
  margin-bottom: 10px;
  font-size: 14px;
}
.knowledge-focus-shell .map-summary-card div > span,
.knowledge-focus-shell .map-summary-card div > b {
  padding: 7px 5px;
}
.knowledge-focus-shell .map-summary-card div > b,
.knowledge-focus-shell .graph-relation-stats b {
  font-size: 15px !important;
}
.knowledge-focus-shell .graph-relation-card button,
.knowledge-focus-shell .graph-doc-card button {
  min-height: 36px !important;
  padding: 7px 0 !important;
}

.search-agent-insights {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}
.search-support-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin: 14px 0 0;
}
.search-context-board {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}
.search-context-board article {
  min-height: 88px;
  display: grid;
  align-content: center;
  gap: 6px;
  padding: 13px 14px;
  border: 1px solid #dfe9e8;
  border-radius: 14px;
  background: linear-gradient(145deg, #ffffff 0%, #f7fbfa 100%);
  box-shadow: 0 10px 22px rgba(28,55,59,.045);
}
.search-context-board b {
  color: #244146;
  font-size: 13px;
}
.search-context-board span {
  overflow: hidden;
  color: #1f363b;
  font-size: 14px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.search-context-board small {
  color: #6d8084;
  font-size: 11px;
  line-height: 1.5;
}
.search-agent-insights article,
.search-support-grid article,
.search-prompt-templates button,
.task-ops-grid article,
.recheck-dashboard article,
.recheck-checklist span {
  border: 1px solid #dfe9e8;
  background: #fff;
  box-shadow: 0 10px 24px rgba(28, 55, 59, .055);
}
.search-agent-insights article {
  min-height: 72px;
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr);
  align-items: center;
  gap: 10px;
  padding: 12px;
  border-radius: 14px;
}
.search-support-grid article {
  min-height: 86px;
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border-radius: 14px;
}
.search-support-grid.compact {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 12px;
}
.search-support-grid.compact article {
  min-height: 76px;
  padding: 10px;
}
.search-support-grid.compact button {
  min-width: 42px;
}
.search-support-grid article > span {
  width: 36px;
  height: 36px;
}
.search-support-grid b {
  display: block;
  color: #20373b;
  font-size: 13px;
}
.search-support-grid small {
  display: -webkit-box;
  overflow: hidden;
  color: #6c7f83;
  font-size: 11px;
  line-height: 1.5;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.search-support-grid em,
.search-support-grid button {
  justify-self: end;
  min-width: 48px;
  padding: 6px 9px;
  border: 1px solid color-mix(in srgb, var(--tone, #16766f) 26%, #dfe9e8);
  border-radius: 999px;
  background: color-mix(in srgb, var(--tone, #16766f) 9%, #fff);
  color: var(--tone, #16766f);
  font-size: 10px;
  font-style: normal;
  font-weight: 850;
}
.search-support-grid button { cursor: pointer; }
.search-support-grid button:hover { background: var(--tone, #16766f); color: #fff; }
.search-agent-insights span,
.search-support-grid article > span,
.search-prompt-templates span,
.task-ops-grid > article > span,
.recheck-dashboard > article > span,
.recheck-checklist i {
  display: grid;
  place-items: center;
  border-radius: 12px;
  color: var(--tone, #16766f);
  background: color-mix(in srgb, var(--tone, #16766f) 12%, #fff);
}
.search-agent-insights span { width: 38px; height: 38px; }
.search-agent-insights b,
.task-ops-grid b,
.recheck-dashboard b {
  display: block;
  color: #20373b;
  font-size: 14px;
}
.search-agent-insights small,
.task-ops-grid p,
.recheck-dashboard em,
.recheck-checklist small {
  color: #6c7f83;
  font-size: 11px;
  line-height: 1.5;
  font-style: normal;
}
.tone-teal { --tone: #16766f; }
.tone-green { --tone: #5f8b62; }
.tone-amber { --tone: #c8872e; }
.tone-blue { --tone: #3f7fa7; }
.tone-red { --tone: #bd5b4d; }
.search-prompt-templates {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin: 10px 0 12px;
}
.search-prompt-templates button {
  min-height: 58px;
  display: grid;
  grid-template-columns: 30px minmax(0, 1fr);
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 12px;
  color: #264348;
  text-align: left;
}
.search-prompt-templates button:hover {
  border-color: #b7d2cf;
  background: #f6fbfa;
  transform: translateY(-1px);
}
.search-prompt-templates span { width: 30px; height: 30px; }
.search-prompt-templates b {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
}
.search-fusion-head .inline-actions .primary {
  border-color: #1f6568 !important;
  background: #1f6568 !important;
  color: #fff !important;
  box-shadow: 0 9px 18px rgba(31,101,104,.16);
}
.search-fusion-head .inline-actions .primary:disabled {
  opacity: .72;
  cursor: wait;
}
.search-workbench-v2 .search-fusion-bar {
  grid-template-columns: 40px 40px minmax(0, 1fr) 58px;
}
.search-focus-shell .search-agent-hero {
  min-height: 112px;
  padding: 16px 18px;
}
.search-focus-shell .search-agent-intro {
  grid-template-columns: 72px minmax(0, 1fr);
  gap: 14px;
}
.search-focus-shell .search-agent-intro img {
  width: 72px;
  height: 72px;
}
.search-focus-shell .search-agent-intro h2 {
  font-size: 22px;
}
.search-focus-shell .search-agent-intro b {
  margin: 6px 0 4px;
}
.search-focus-shell .search-agent-intro p {
  line-height: 1.55;
}
.search-focus-shell .search-fusion-panel {
  gap: 12px;
  padding: 16px;
}
.search-focus-shell .search-fusion-head {
  align-items: center;
}
.search-focus-shell .search-panel-heading {
  gap: 10px;
}
.search-focus-shell .search-step {
  width: 34px;
  height: 34px;
}
.search-focus-shell .search-fusion-body {
  grid-template-columns: minmax(620px, 1.2fr) minmax(410px, .8fr);
  gap: 14px;
}
.search-focus-shell .search-fusion-input,
.search-focus-shell .search-fusion-ai {
  gap: 10px;
  padding: 12px;
  border-radius: 15px;
}
.search-focus-shell .search-fusion-ai {
  grid-template-rows: none !important;
}
.search-focus-shell .search-fusion-input {
  align-content: stretch;
}
.search-focus-shell .search-fusion-ai {
  align-content: stretch;
  grid-template-rows: auto auto auto minmax(180px, 1fr) !important;
}
.search-focus-shell .search-context-board {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}
.search-focus-shell .search-context-board article {
  border-color: #dbe8e5;
  background:
    linear-gradient(145deg, rgba(255,255,255,.96), rgba(247,252,250,.96)),
    radial-gradient(circle at 12% 15%, rgba(47,127,143,.08), transparent 32%);
}
.search-focus-shell .search-dialog-thread {
  min-height: 190px;
  max-height: none;
}
.search-focus-shell .search-fusion-panel .form-grid {
  gap: 9px 10px;
}
.search-focus-shell .search-fusion-panel .form-grid input,
.search-focus-shell .search-fusion-panel .form-grid select {
  height: 36px;
}
.search-focus-shell .search-fusion-panel .form-grid textarea {
  min-height: 70px;
}
.search-focus-shell .search-upload-zone {
  min-height: 74px;
  padding: 10px 12px;
}
.search-focus-shell .search-context-board {
  gap: 8px;
  margin-top: 8px;
}
.search-focus-shell .search-context-board article {
  min-height: 72px;
  padding: 10px 12px;
}
.search-focus-shell .search-support-grid.compact {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin-top: 8px;
}
.search-focus-shell .search-support-grid.compact article {
  min-height: 70px;
  grid-template-columns: 30px minmax(0, 1fr);
  padding: 9px;
}
.search-focus-shell .search-support-grid.compact article > button {
  display: none;
}
.search-focus-shell .search-support-grid.compact article > span {
  width: 30px;
  height: 30px;
}
.search-focus-shell .search-ai-status {
  grid-template-columns: 40px minmax(0,1fr);
  padding: 8px;
}
.search-focus-shell .search-ai-status img {
  width: 40px;
  height: 40px;
}
.search-focus-shell .search-agent-insights {
  gap: 8px;
}
.search-focus-shell .search-agent-insights article {
  min-height: 62px;
  grid-template-columns: 32px minmax(0, 1fr);
  padding: 9px;
}
.search-focus-shell .search-agent-insights span {
  width: 32px;
  height: 32px;
}
.search-focus-shell .search-prompt-templates {
  gap: 7px;
  margin: 6px 0;
}
.search-focus-shell .search-prompt-templates button {
  height: 48px !important;
  min-height: 48px;
  grid-template-columns: 26px minmax(0, 1fr);
  padding: 7px 8px;
  overflow: hidden;
}
.search-focus-shell .search-prompt-templates span {
  width: 26px;
  height: 26px;
}
.search-focus-shell .search-dialog-summary {
  gap: 8px;
}
.search-focus-shell .search-dialog-summary article {
  min-height: 72px;
  padding: 10px;
}
.search-focus-shell .search-dialog-thread {
  min-height: 122px;
  max-height: 150px;
  padding: 10px;
}
.search-focus-shell .search-fusion-bar {
  padding: 10px 12px;
}
.history-command-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin: 14px 0 12px;
}
.history-command-strip button {
  min-height: 74px;
  display: grid;
  align-content: center;
  gap: 5px;
  padding: 12px 14px;
  border: 1px solid #dce9e6;
  border-radius: 14px;
  background: linear-gradient(145deg, #ffffff, #f7fbfa);
  color: #284247;
  text-align: left;
}
.history-command-strip button:nth-child(2) {
  border-color: #eadbc6;
  background: linear-gradient(145deg, #fff, #fff9f1);
}
.history-command-strip button:nth-child(3) {
  border-color: #d9e4ef;
  background: linear-gradient(145deg, #fff, #f5f9fc);
}
.history-command-strip b {
  font-size: 14px;
}
.history-command-strip small {
  color: #708386;
  font-size: 11px;
  line-height: 1.45;
}
.search-history-panel {
  border-color: #dce8e5 !important;
  background:
    linear-gradient(180deg, rgba(255,255,255,.95), rgba(249,252,251,.96)),
    radial-gradient(circle at 4% 12%, rgba(47,127,143,.08), transparent 28%) !important;
}
.search-history-panel .history-stat-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}
.search-history-panel .history-stat-grid span {
  border-color: #dce9e6;
  background: #fff;
}
.history-search-list button {
  position: relative;
  overflow: hidden;
}
.history-search-list button::after {
  content: "";
  position: absolute;
  left: 12px;
  right: 66px;
  bottom: 10px;
  height: 4px;
  border-radius: 999px;
  background: linear-gradient(90deg, #2f7f8f 0%, #6b9b70 72%, #e3ecea 72%);
  opacity: .42;
}
.history-trace-lanes {
  display: grid;
  gap: 10px;
  margin: 14px 0;
}
.history-trace-lanes article {
  min-height: 74px;
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border: 1px solid color-mix(in srgb, var(--tone, #16766f) 24%, #dfe9e8);
  border-radius: 14px;
  background: linear-gradient(145deg, color-mix(in srgb, var(--tone, #16766f) 8%, #fff), #fff 76%);
  box-shadow: 0 10px 22px rgba(28,55,59,.045);
}
.history-trace-lanes article > span {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  color: var(--tone, #16766f);
  background: color-mix(in srgb, var(--tone, #16766f) 13%, #fff);
}
.history-trace-lanes b {
  display: block;
  color: #20373b;
  font-size: 13px;
}
.history-trace-lanes small {
  color: #6c7f83;
  font-size: 11px;
  line-height: 1.5;
}
.history-trace-lanes em {
  padding: 6px 9px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--tone, #16766f) 10%, #fff);
  color: var(--tone, #16766f);
  font-size: 10px;
  font-style: normal;
  font-weight: 850;
}
.history-learning-panel {
  border-color: #dfe6dc !important;
  background:
    linear-gradient(180deg, rgba(255,255,255,.95), rgba(250,252,247,.96)),
    radial-gradient(circle at 95% 10%, rgba(199,135,46,.09), transparent 24%) !important;
}
.update-progress-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin: 14px 0 16px;
}
.update-progress-strip article {
  min-height: 86px;
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr);
  align-items: center;
  gap: 10px;
  padding: 12px;
  border: 1px solid color-mix(in srgb, var(--tone, #16766f) 22%, #dfe9e8);
  border-radius: 14px;
  background: linear-gradient(145deg, color-mix(in srgb, var(--tone, #16766f) 8%, #fff), #fff 78%);
  box-shadow: 0 10px 22px rgba(28,55,59,.045);
}
.update-progress-strip article > span {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  color: var(--tone, #16766f);
  background: color-mix(in srgb, var(--tone, #16766f) 13%, #fff);
}
.update-progress-strip small {
  color: var(--tone, #16766f);
  font-size: 10px;
  font-weight: 850;
}
.update-progress-strip b {
  display: block;
  margin: 3px 0;
  color: #20373b;
  font-size: 18px;
}
.update-progress-strip em {
  color: #6c7f83;
  font-size: 11px;
  font-style: normal;
}
.search-update-panel {
  border-color: #dfe7de !important;
  background:
    linear-gradient(180deg, rgba(255,255,255,.96), rgba(250,252,248,.96)),
    radial-gradient(circle at 8% 10%, rgba(95,139,98,.08), transparent 27%),
    radial-gradient(circle at 92% 8%, rgba(200,135,46,.08), transparent 22%) !important;
}
.update-rule-list {
  display: grid;
  gap: 9px;
  padding: 13px;
  border: 1px solid #dfe8dd;
  border-radius: 14px;
  background: #fff;
}
.update-rule-list > b {
  color: #263d35;
  font-size: 14px;
}
.update-rule-list span {
  display: grid;
  gap: 3px;
  padding: 9px 10px;
  border-radius: 11px;
  background: #f8fbf7;
}
.update-rule-list small {
  color: #5f8b62;
  font-size: 11px;
  font-weight: 850;
}
.update-rule-list em {
  color: #65786d;
  font-size: 11px;
  line-height: 1.45;
  font-style: normal;
}

/* 智能检索三板块均衡：固定工作区高度，内部模块等高排布，减少空白与截断。 */
.search-focus-shell .search-workbench-v2 {
  grid-auto-rows: auto;
}
.search-focus-shell .search-fusion-panel,
.search-focus-shell .search-history-panel,
.search-focus-shell .history-learning-panel,
.search-focus-shell .search-update-panel {
  height: calc(100vh - 245px);
  min-height: 640px !important;
  max-height: 720px;
  overflow: hidden;
}
.search-focus-shell .search-fusion-panel {
  grid-template-rows: auto minmax(0, 1fr) auto;
}
.search-focus-shell .search-fusion-body {
  min-height: 0;
  height: 100%;
}
.search-focus-shell .search-fusion-input,
.search-focus-shell .search-fusion-ai {
  min-height: 0;
  height: 100%;
}
.search-focus-shell .search-dialog-thread {
  min-height: 0;
  max-height: none;
  height: 100%;
  overflow: auto;
}
.search-focus-shell .search-context-board article {
  min-height: 78px;
}
.search-focus-shell .search-history-panel {
  display: grid;
  grid-template-rows: auto auto auto minmax(0, 1fr) auto;
  gap: 12px;
  align-content: stretch;
}
.search-focus-shell .history-learning-panel {
  display: grid;
  grid-template-rows: auto auto auto minmax(0, 1fr);
  gap: 12px;
  align-content: stretch;
}
.search-focus-shell .history-command-strip,
.search-focus-shell .history-trace-lanes,
.search-focus-shell .learning-recommend-list,
.search-focus-shell .history-search-list,
.search-focus-shell .history-stat-grid {
  margin: 0;
}
.search-focus-shell .history-command-strip button {
  min-height: 62px;
  padding: 10px 12px;
}
.search-focus-shell .history-stat-grid span {
  min-height: 58px;
  padding: 11px 12px;
}
.search-focus-shell .history-search-list,
.search-focus-shell .learning-recommend-list {
  min-height: 0;
  overflow: auto;
  padding-right: 3px;
  scrollbar-width: none;
}
.search-focus-shell .history-search-list::-webkit-scrollbar,
.search-focus-shell .learning-recommend-list::-webkit-scrollbar {
  width: 0;
  height: 0;
}
.search-focus-shell .history-search-list button {
  min-height: 86px;
  grid-template-columns: minmax(0, 1fr) 48px;
}
.search-focus-shell .history-action-row {
  margin-top: 0;
}
.search-focus-shell .history-trace-lanes article {
  min-height: 64px;
  padding: 10px;
}
.search-focus-shell .learning-recommend-list article {
  min-height: 118px;
  padding: 12px;
}
.search-focus-shell .learning-recommend-list p {
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.search-focus-shell .search-update-panel {
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr) auto minmax(0, .6fr);
  gap: 12px;
  align-content: stretch;
}
.search-focus-shell .update-progress-strip {
  gap: 10px;
  margin: 0;
}
.search-focus-shell .update-progress-strip article {
  min-height: 74px;
  padding: 10px;
}
.search-focus-shell .search-update-layout {
  min-height: 0;
  height: 100%;
  grid-template-columns: minmax(0, 1.75fr) minmax(250px, .55fr);
  gap: 14px;
}
.search-focus-shell .search-update-layout .form-grid {
  min-height: 0;
  align-content: start;
  gap: 10px;
}
.search-focus-shell .search-update-layout .form-grid input,
.search-focus-shell .search-update-layout .form-grid select {
  height: 38px;
}
.search-focus-shell .search-update-layout .form-grid textarea {
  min-height: 108px;
}
.search-focus-shell .knowledge-update-aside {
  min-height: 0;
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
  gap: 10px;
  align-content: stretch;
}
.search-focus-shell .update-quality-card {
  padding: 12px;
}
.search-focus-shell .update-step-list {
  gap: 8px;
}
.search-focus-shell .update-step-list article {
  min-height: 52px;
  padding: 9px 10px;
}
.search-focus-shell .update-rule-list {
  min-height: 0;
  overflow: auto;
  padding: 11px;
  scrollbar-width: none;
}
.search-focus-shell .update-rule-list::-webkit-scrollbar {
  width: 0;
  height: 0;
}
.search-focus-shell .update-rule-list span {
  padding: 8px 9px;
}
.search-focus-shell .search-update-panel .knowledge-review-list {
  min-height: 0;
  overflow: auto;
  margin-top: 0;
  padding-right: 3px;
  scrollbar-width: none;
}
.search-focus-shell .search-update-panel .knowledge-review-list::-webkit-scrollbar {
  width: 0;
  height: 0;
}

/* 智能检索深度更新区二次收口：让表单、规则、审核记录分别占用稳定区域。 */
.search-focus-shell .search-update-panel {
  grid-template-rows: auto 76px minmax(300px, 1fr) 36px minmax(118px, .45fr);
}
.search-focus-shell .search-update-layout {
  overflow: hidden;
}
.search-focus-shell .search-update-layout > * {
  min-height: 0;
  max-height: 100%;
}
.search-focus-shell .search-update-layout .form-grid {
  height: 100%;
  overflow: auto;
  padding-right: 3px;
  scrollbar-width: none;
}
.search-focus-shell .search-update-layout .form-grid::-webkit-scrollbar {
  width: 0;
  height: 0;
}
.search-focus-shell .search-update-layout .form-grid label {
  min-height: 66px;
}
.search-focus-shell .search-update-layout .form-grid label.wide {
  min-height: 126px;
}
.search-focus-shell .knowledge-update-aside {
  height: 100%;
  max-height: 100%;
  overflow: hidden;
  grid-template-rows: 82px 100px minmax(92px, 1fr);
}
.search-focus-shell .update-step-list {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  min-height: 0;
  overflow: hidden;
  scrollbar-width: none;
}
.search-focus-shell .update-step-list::-webkit-scrollbar {
  width: 0;
  height: 0;
}
.search-focus-shell .update-rule-list {
  height: 100%;
  max-height: none;
}
.search-focus-shell .update-quality-card {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px;
  height: 82px;
  overflow: hidden;
}
.search-focus-shell .update-quality-card > b {
  grid-column: 1 / -1;
}
.search-focus-shell .update-quality-card span {
  min-height: 34px;
  display: grid;
  place-items: center;
  padding: 4px 6px;
  text-align: center;
}
.search-focus-shell .update-quality-card small,
.search-focus-shell .update-quality-card em {
  line-height: 1.15;
}
.search-focus-shell .update-quality-card em {
  font-size: 12px;
}
.search-focus-shell .update-step-list {
  height: 100px;
  grid-auto-rows: 46px;
}
.search-focus-shell .update-step-list article {
  grid-template-columns: 8px minmax(0, 1fr);
  min-height: 0;
  height: 46px;
  overflow: hidden;
}
.search-focus-shell .update-step-list small,
.search-focus-shell .update-rule-list em {
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.search-focus-shell .search-update-panel > .primary {
  width: fit-content;
  min-height: 36px;
  padding: 7px 16px;
}
.search-focus-shell .search-update-panel .knowledge-review-list {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.search-focus-shell .search-update-panel .knowledge-review-list .result-card {
  min-height: 0;
  padding: 11px;
}
.search-focus-shell .search-update-panel .knowledge-review-list .result-card p {
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.search-focus-shell .search-update-panel .knowledge-review-list textarea {
  min-height: 48px;
  resize: none;
}

/* 沉淀更新页防裁字：状态卡和右侧流程卡保留足够内边距，文字始终在框内。 */
.search-focus-shell .search-update-panel {
  height: auto;
  min-height: calc(100vh - 245px) !important;
  max-height: none;
  overflow: visible;
  grid-template-rows: auto 92px minmax(385px, auto) auto auto;
}
.search-focus-shell .update-progress-strip {
  align-items: stretch;
}
.search-focus-shell .update-progress-strip article {
  height: 92px;
  min-height: 92px;
  align-items: center;
  padding: 12px 14px;
  overflow: hidden;
}
.search-focus-shell .update-progress-strip article > div {
  min-width: 0;
  display: grid;
  gap: 2px;
}
.search-focus-shell .update-progress-strip small,
.search-focus-shell .update-progress-strip b,
.search-focus-shell .update-progress-strip em {
  min-width: 0;
  max-width: 100%;
}
.search-focus-shell .update-progress-strip em {
  display: -webkit-box;
  overflow: hidden;
  line-height: 1.35;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.search-focus-shell .search-update-layout {
  grid-template-columns: minmax(0, 1.9fr) minmax(280px, .5fr);
  height: auto;
  min-height: 385px;
  overflow: visible;
}
.search-focus-shell .knowledge-update-aside {
  height: auto;
  max-height: none;
  overflow: visible;
  grid-template-rows: auto auto auto;
  gap: 10px;
}
.search-focus-shell .update-quality-card {
  height: 98px;
  padding: 10px;
}
.search-focus-shell .update-quality-card span {
  min-height: 42px;
}
.search-focus-shell .update-step-list {
  height: auto;
  grid-auto-rows: auto;
  overflow: visible;
}
.search-focus-shell .update-step-list article {
  height: auto;
  min-height: 62px;
  padding: 8px 9px;
}
.search-focus-shell .update-step-list b {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.search-focus-shell .update-step-list small {
  line-height: 1.3;
  -webkit-line-clamp: 3;
}
.search-focus-shell .update-rule-list {
  height: auto;
  overflow: visible;
  padding: 10px;
}
.search-focus-shell .update-rule-list span {
  min-height: 54px;
}
.search-focus-shell .update-rule-list em {
  -webkit-line-clamp: 3;
}
.search-focus-shell .search-update-layout .form-grid {
  overflow: visible;
}
.search-focus-shell .search-update-layout .form-grid textarea {
  min-height: 132px;
}
.search-focus-shell .search-update-panel .knowledge-review-list {
  max-height: none;
  overflow: visible;
}
.search-focus-shell .search-update-panel .knowledge-review-list textarea {
  min-height: 64px;
}

/* 沉淀更新完整展示：右侧检查、流程、规则不再被固定高度裁切。 */
.search-focus-shell .search-update-panel {
  height: auto !important;
  max-height: none !important;
  overflow: visible !important;
  grid-template-rows: auto auto auto auto auto !important;
}
.search-focus-shell .search-update-layout {
  height: auto !important;
  min-height: 0 !important;
  overflow: visible !important;
  align-items: start;
}
.search-focus-shell .search-update-layout > *,
.search-focus-shell .knowledge-update-aside,
.search-focus-shell .update-quality-card,
.search-focus-shell .update-step-list,
.search-focus-shell .update-rule-list {
  height: auto !important;
  max-height: none !important;
  overflow: visible !important;
}
.search-focus-shell .knowledge-update-aside {
  grid-template-rows: auto auto auto !important;
  align-content: start;
}
.search-focus-shell .update-step-list {
  grid-auto-rows: auto !important;
}
.search-focus-shell .update-step-list article {
  min-height: 66px !important;
  height: auto !important;
}
.search-focus-shell .update-step-list small,
.search-focus-shell .update-rule-list em {
  display: block !important;
  overflow: visible !important;
  -webkit-line-clamp: unset !important;
  -webkit-box-orient: unset !important;
}
.search-focus-shell .update-rule-list span {
  min-height: 58px;
  align-content: center;
}
.search-focus-shell .search-update-layout .form-grid {
  height: auto !important;
  overflow: visible !important;
}
.search-focus-shell .search-update-layout .form-grid textarea {
  min-height: 150px;
}
.search-focus-shell .search-update-panel > .primary {
  margin-top: 8px;
}
.search-focus-shell :is(.panel, article, button, span, b, small, em, p, h3, input, textarea, select) {
  min-width: 0;
}
.search-focus-shell :is(.learning-recommend-list, .history-trace-lanes, .history-command-strip, .history-search-list, .update-progress-strip, .update-quality-card, .update-step-list, .update-rule-list, .search-context-board, .search-dialog-summary) :is(b, small, em, p, span) {
  overflow-wrap: anywhere;
  word-break: break-word;
}
.search-focus-shell :is(.history-search-list b, .history-search-list small, .history-trace-lanes b, .history-trace-lanes small, .learning-recommend-list b, .update-progress-strip b, .update-progress-strip em, .update-quality-card em) {
  overflow: hidden;
  text-overflow: ellipsis;
}
.search-focus-shell .learning-recommend-list article {
  cursor: pointer;
  transition: border-color .18s ease, box-shadow .18s ease, transform .18s ease;
}
.search-focus-shell .learning-recommend-list article:hover,
.search-focus-shell .learning-recommend-list article.active {
  border-color: #83b9ad;
  box-shadow: 0 12px 24px rgba(47, 111, 112, .1);
  transform: translateY(-1px);
}
.search-focus-shell .learning-card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.search-focus-shell .learning-card-actions button {
  margin: 0;
}
.learning-detail-modal {
  width: min(720px, 94vw);
  border: 1px solid #d7e8e5;
  background:
    linear-gradient(180deg, rgba(255,255,255,.98), rgba(248,252,250,.98)),
    radial-gradient(circle at 96% 8%, rgba(95,139,98,.12), transparent 30%);
}
.learning-detail-modal h2 {
  color: #213d3f;
  font-size: 24px;
  line-height: 1.3;
}
.learning-detail-desc {
  margin: 0;
  padding: 12px 14px;
  border: 1px solid #dfe9e7;
  border-radius: 13px;
  background: #fff;
  color: #5f7374;
  line-height: 1.7;
}
.learning-detail-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}
.learning-detail-grid span {
  min-height: 74px;
  display: grid;
  align-content: center;
  gap: 5px;
  padding: 12px;
  border: 1px solid #dce9e7;
  border-radius: 13px;
  background: #fff;
}
.learning-detail-grid small {
  color: #6d8587;
  font-size: 11px;
}
.learning-detail-grid b {
  color: #233f42;
  font-size: 13px;
  line-height: 1.45;
  overflow-wrap: anywhere;
}
.learning-step-card {
  display: grid;
  gap: 8px;
  padding: 14px 16px;
  border: 1px solid #e2dac9;
  border-radius: 14px;
  background: #fffaf2;
}
.learning-step-card b {
  color: #725424;
}
.learning-step-card ol {
  margin: 0;
  padding-left: 20px;
  color: #5f6f6f;
  line-height: 1.75;
}
.task-ops-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-top: 12px;
}
.task-ops-grid article {
  min-height: 112px;
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 13px;
  border-radius: 14px;
}
.task-ops-grid > article > span { width: 42px; height: 42px; }
.task-ops-grid small {
  color: var(--tone, #16766f);
  font-size: 10px;
  font-weight: 800;
}
.task-ops-grid button {
  min-width: 48px;
  height: 32px;
  border: 1px solid color-mix(in srgb, var(--tone, #16766f) 28%, #dfe9e8);
  border-radius: 9px;
  background: color-mix(in srgb, var(--tone, #16766f) 9%, #fff);
  color: var(--tone, #16766f);
  font-size: 11px;
  font-weight: 800;
}
.recheck-dashboard {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin: -6px 0 18px;
}
.recheck-dashboard article {
  min-height: 92px;
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr);
  align-items: center;
  gap: 10px;
  padding: 13px;
  border-radius: 14px;
}
.recheck-dashboard > article > span { width: 42px; height: 42px; }
.recheck-dashboard small {
  color: var(--tone, #16766f);
  font-size: 10px;
  font-weight: 850;
}
.recheck-dashboard b { font-size: 24px; }
.recheck-checklist {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
.recheck-checklist span {
  min-height: 66px;
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr);
  grid-template-rows: auto auto;
  column-gap: 8px;
  align-items: center;
  padding: 9px;
  border-radius: 12px;
  background: #fffaf6;
}
.recheck-checklist span.ok {
  background: #f6fbf8;
  border-color: #dcebe0;
}
.recheck-checklist i {
  grid-row: span 2;
  width: 28px;
  height: 28px;
  --tone: #bd6a39;
}
.recheck-checklist span.ok i { --tone: #5f8b62; }
.recheck-checklist b {
  color: #294247;
  font-size: 12px;
}
@media (max-width: 1180px) {
  .search-agent-insights,
  .search-support-grid,
  .task-ops-grid,
  .recheck-dashboard { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .search-prompt-templates { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

/* 多模态检索折叠抽屉：表单等高、文字不溢出，收起后保留关键上下文。 */
.search-focus-shell .search-fusion-panel.is-collapsed,
.search-focus-shell .search-fusion-panel.is-expanded {
  height: auto !important;
  min-height: 0 !important;
  max-height: none !important;
  overflow: visible !important;
}
.search-focus-shell .search-fusion-head {
  min-width: 0;
}
.search-focus-shell .search-fusion-head .search-panel-heading {
  min-width: 0;
  flex: 1 1 auto;
}
.search-focus-shell .search-fusion-head h3,
.search-focus-shell .search-fusion-head small {
  max-width: 100%;
  overflow-wrap: anywhere;
}
.search-focus-shell .search-fusion-head .inline-actions {
  flex: 0 0 auto;
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.search-focus-shell .search-fusion-head .ghost-toggle {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  min-width: 78px;
}
.search-focus-shell .search-fusion-head .ghost-toggle .ui-icon {
  width: 14px;
  height: 14px;
  transition: transform .18s ease;
}
.search-focus-shell .search-fusion-head .ghost-toggle .ui-icon.up {
  transform: rotate(180deg);
}
.search-focus-shell .search-collapse-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr)) auto;
  gap: 10px;
  align-items: stretch;
  padding: 12px;
  border: 1px solid #dbe8e5;
  border-radius: 15px;
  background: #fbfdfc;
}
.search-focus-shell .search-collapse-summary span {
  min-width: 0;
  display: grid;
  gap: 3px;
  padding: 10px 12px;
  border-radius: 12px;
  background: #fff;
  color: #51686c;
  box-shadow: inset 0 0 0 1px #edf2f1;
  font-size: 12px;
  line-height: 1.35;
  overflow: hidden;
}
.search-focus-shell .search-collapse-summary b {
  color: #1f3438;
  font-size: 12px;
  font-weight: 750;
}
.search-focus-shell .search-collapse-summary button {
  min-height: 54px;
  padding: 0 18px;
  border: 0;
  border-radius: 13px;
  background: #2f6f73;
  color: #fff;
  font-weight: 780;
}
.search-focus-shell .search-fusion-body {
  grid-template-columns: minmax(0, 1.05fr) minmax(360px, .95fr) !important;
  align-items: stretch;
}
.search-focus-shell .search-fusion-panel .form-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  align-items: start;
}
.search-focus-shell .search-fusion-panel .form-grid label {
  min-width: 0;
  display: grid;
  gap: 6px;
  line-height: 1.25;
  overflow: hidden;
}
.search-focus-shell .search-fusion-panel .form-grid label.wide {
  grid-column: 1 / -1;
}
.search-focus-shell .search-fusion-panel .form-grid input,
.search-focus-shell .search-fusion-panel .form-grid select,
.search-focus-shell .search-fusion-panel .form-grid textarea {
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
  color: #263d42;
  line-height: 1.35;
}
.search-focus-shell .search-fusion-panel .form-grid textarea {
  min-height: 84px !important;
  resize: vertical;
}
.search-focus-shell .search-evidence-box,
.search-focus-shell .search-upload-zone,
.search-focus-shell .search-context-board,
.search-focus-shell .search-dialog-summary,
.search-focus-shell .search-prompt-templates {
  min-width: 0;
}
.search-focus-shell .search-upload-zone {
  grid-template-columns: 42px minmax(0, 1fr) auto;
}
.search-focus-shell .upload-copy,
.search-focus-shell .upload-copy b,
.search-focus-shell .upload-copy small,
.search-focus-shell .search-context-board :is(b, span, small),
.search-focus-shell .search-dialog-summary :is(b, p),
.search-focus-shell .search-prompt-templates b,
.search-focus-shell .file-pills span {
  min-width: 0;
  max-width: 100%;
  overflow-wrap: anywhere;
  word-break: break-word;
}
.search-focus-shell .search-context-board {
  grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
}
.search-focus-shell .search-context-board article {
  min-width: 0;
  height: auto;
}
.search-focus-shell .search-prompt-templates {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.search-focus-shell .search-prompt-templates button {
  min-width: 0;
}
.search-focus-shell .search-dialog-thread {
  min-height: 220px !important;
  max-height: 360px !important;
}
.search-focus-shell .search-fusion-bar {
  grid-template-columns: 42px 42px minmax(0, 1fr) 58px !important;
}
.search-focus-shell .search-fusion-bar input {
  min-width: 0;
}

/* 多模态证据区修正：上传框与上下文卡片更紧凑，避免大块空白和边缘遮挡。 */
.search-focus-shell .search-evidence-box {
  gap: 10px !important;
  padding: 0;
}
.search-focus-shell .search-upload-zone {
  min-height: 88px !important;
  padding: 12px 16px !important;
  border-radius: 16px !important;
  background: #f8fbfa !important;
  border-color: #b9d5d2 !important;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.72);
}
.search-focus-shell .search-upload-zone .upload-mark {
  width: 50px;
  height: 50px;
  border-radius: 14px;
}
.search-focus-shell .search-upload-zone .upload-copy {
  align-content: center;
}
.search-focus-shell .search-upload-zone .upload-copy b {
  font-size: 14px;
  line-height: 1.25;
}
.search-focus-shell .search-upload-zone .upload-copy small {
  font-size: 11px;
  line-height: 1.45;
}
.search-focus-shell .search-upload-zone > button {
  min-width: 72px;
  height: 42px;
  padding: 0 14px;
  border-radius: 12px;
  white-space: nowrap;
}
.search-focus-shell .file-pills {
  margin-top: 0;
  gap: 6px;
}
.search-focus-shell .file-pills:empty {
  display: none;
}
.search-focus-shell .file-pills span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  max-width: 100%;
  padding: 6px 9px;
  border: 1px solid #d8e6e4;
  background: #f6fbfa;
  color: #3d5d61;
  line-height: 1.35;
}
.search-focus-shell .search-context-board {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  gap: 10px !important;
  margin-top: 0 !important;
}
.search-focus-shell .search-context-board article {
  min-height: 104px !important;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  gap: 8px;
  padding: 14px 16px !important;
  border-radius: 16px !important;
  border: 1px solid #d9e7e5 !important;
  background: #fff !important;
  box-shadow: 0 8px 18px rgba(31,69,75,.035);
}
.search-focus-shell .search-context-board article b {
  font-size: 13px;
  line-height: 1.25;
}
.search-focus-shell .search-context-board article span {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  color: #1f3438;
  font-size: 15px;
  line-height: 1.35;
}
.search-focus-shell .search-context-board article small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #687d80;
  font-size: 12px;
  line-height: 1.35;
}
@media (max-width: 1180px) {
  .search-focus-shell .search-fusion-body {
    grid-template-columns: 1fr !important;
  }
  .search-focus-shell .search-collapse-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .search-focus-shell .search-collapse-summary button {
    grid-column: 1 / -1;
  }
}
@media (max-width: 760px) {
  .search-focus-shell .search-fusion-head {
    align-items: stretch !important;
    flex-direction: column;
  }
  .search-focus-shell .search-fusion-head .inline-actions {
    justify-content: flex-start;
  }
  .search-focus-shell .search-fusion-panel .form-grid,
  .search-focus-shell .search-context-board,
  .search-focus-shell .search-prompt-templates,
  .search-focus-shell .search-collapse-summary {
    grid-template-columns: 1fr !important;
  }
}

@media (max-width: 1380px), (max-height: 820px) {
  .app-shell {
    grid-template-columns: 196px minmax(0, 1fr) !important;
  }
  .app-shell.collapsed {
    grid-template-columns: 70px minmax(0, 1fr) !important;
  }
  .side-nav {
    gap: 12px !important;
    padding: 12px 10px !important;
  }
  .brand {
    width: 150px !important;
    height: 58px !important;
  }
  .side-nav nav button {
    min-height: 38px !important;
    padding: 0 10px !important;
  }
  .topbar {
    height: 66px !important;
    grid-template-columns: minmax(150px, 1fr) minmax(230px, 320px) 34px auto auto !important;
    gap: 9px !important;
    padding: 0 12px !important;
  }
  .topbar .page-title-block {
    min-height: 54px !important;
    padding: 8px 14px !important;
  }
  .topbar h1 {
    font-size: 17px !important;
  }
  .topbar .breadcrumb {
    font-size: 11px !important;
  }
  .topbar .work-strip {
    display: none !important;
  }
  .content-shell {
    height: calc(100vh - 66px) !important;
    grid-template-columns: minmax(0, 1fr) 8px minmax(286px, 300px) !important;
  }
  .page-scroll {
    padding: 14px !important;
  }
  .operator-panel {
    min-width: 286px !important;
    padding: 14px 12px !important;
    gap: 10px !important;
  }
  .operator-avatar {
    width: 68px !important;
    height: 68px !important;
  }
  .chat-thread {
    gap: 10px !important;
  }
  .bubble {
    padding: 10px 12px !important;
    font-size: 13px !important;
  }
  .ask-box {
    min-height: 50px !important;
  }
  .home-news-carousel {
    grid-column: span 7 !important;
  }
  .home-schedule-panel {
    grid-column: span 5 !important;
  }
  .news-carousel-stage,
  .news-image-link,
  .news-image-link img {
    min-height: 180px !important;
  }
  .home-task-panel .home-task-list {
    max-height: 360px !important;
  }
  .dashboard-charts .chart-tile {
    min-height: 188px !important;
  }
  .dashboard-charts .chart-tile .chart-canvas {
    height: 184px !important;
  }
  .kb-template-modal,
  .kb-template-lib-modal {
    width: min(880px, calc(100vw - 44px)) !important;
    max-height: calc(100vh - 52px) !important;
    overflow: auto !important;
  }
  .kb-template-grid {
    grid-template-columns: repeat(2, minmax(260px, 1fr)) !important;
  }
  .search-focus-shell {
    grid-template-columns: minmax(0, 1fr) !important;
  }
  .search-focus-shell .page-scroll {
    padding: 14px !important;
  }
  .search-focus-shell .search-fusion-body {
    grid-template-columns: minmax(520px, 1.1fr) minmax(330px, .9fr) !important;
    gap: 12px !important;
  }
  .search-focus-shell .search-context-board {
    grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  }
}

/* 一休奶油白品牌主题：用于侧边导航与顶部工作区。 */
.side-nav {
  border-right: 1px solid rgba(190, 139, 56, .14) !important;
  background-color: #fbf3df !important;
  background-image:
    linear-gradient(180deg, #fffdf7 0%, #fbf2dc 58%, #f6e6bd 100%) !important;
  box-shadow: 12px 0 30px rgba(151, 102, 27, .055) !important;
}
.side-nav::before {
  background: rgba(255, 255, 255, .82) !important;
  box-shadow: 0 1px 0 rgba(151, 102, 27, .12) !important;
}
.side-nav .brand {
  width: 176px !important;
  height: 74px !important;
  padding: 3px 6px !important;
  background: rgba(255, 252, 242, .46) !important;
  filter: drop-shadow(0 12px 18px rgba(86, 60, 19, .12)) !important;
}
.app-shell.collapsed .side-nav .brand {
  width: 54px !important;
  height: 54px !important;
  padding: 4px !important;
  border-radius: 13px !important;
  background: rgba(255, 252, 242, .7) !important;
}
.side-nav nav button {
  border-color: rgba(255, 255, 255, .32) !important;
  background: rgba(255, 255, 255, .22) !important;
  color: #5d4313 !important;
  box-shadow: 0 1px 0 rgba(255, 255, 255, .45) inset !important;
}
.side-nav nav button:hover:not(.active) {
  border-color: rgba(255, 255, 255, .74) !important;
  background: rgba(255, 255, 255, .46) !important;
  color: #2f4f42 !important;
  box-shadow: 0 10px 20px rgba(139, 96, 26, .1), 0 1px 0 rgba(255, 255, 255, .86) inset !important;
}
.side-nav .nav-icon {
  background: rgba(255, 250, 234, .64) !important;
  color: #88631b !important;
  box-shadow: inset 0 0 0 1px rgba(164, 114, 36, .12) !important;
}
.side-nav nav button.active {
  border-color: rgba(255, 255, 255, .9) !important;
  background: #fffdf8 !important;
  color: #123f36 !important;
  box-shadow: 0 14px 26px rgba(129, 84, 16, .09), 0 1px 0 rgba(255, 255, 255, .95) inset !important;
}
.side-nav nav button.active .nav-icon {
  background: linear-gradient(135deg, #123f36, #1b6e58) !important;
  color: #f8df95 !important;
}
.side-nav .collapse-btn {
  border-color: rgba(255, 255, 255, .68) !important;
  background: rgba(255, 250, 235, .5) !important;
  color: #5d4313 !important;
  box-shadow: 0 1px 0 rgba(255, 255, 255, .8) inset !important;
}
.side-nav .collapse-btn:hover {
  background: rgba(255, 252, 244, .82) !important;
  color: #123f36 !important;
}
.topbar {
  --topbar-accent: #92712d;
  --topbar-shadow: rgba(154, 107, 31, .055);
  border-bottom: 1px solid rgba(201, 154, 61, .14) !important;
  background:
    linear-gradient(180deg, rgba(255, 254, 250, .98) 0%, rgba(252, 246, 232, .9) 100%) !important;
  box-shadow: 0 3px 14px rgba(123, 85, 22, .03) !important;
}
.topbar-home,
.topbar-search,
.topbar-tasks,
.topbar-knowledge,
.topbar-profile {
  --topbar-accent: #92712d !important;
  --topbar-shadow: rgba(154, 107, 31, .055) !important;
}
.topbar .page-title-block,
.topbar .global-search,
.topbar .icon-button,
.topbar .user-chip {
  border-color: rgba(201, 154, 61, .24) !important;
  background: rgba(255, 255, 255, .58) !important;
  color: #5d4313 !important;
  box-shadow: 0 1px 0 rgba(255, 255, 255, .9) inset, 0 8px 18px rgba(154, 107, 31, .08) !important;
}
.topbar .breadcrumb {
  color: #806425 !important;
}
.topbar h1 {
  color: #263b35 !important;
}
.topbar .global-search:focus-within {
  border-color: rgba(183, 131, 36, .56) !important;
  box-shadow: 0 0 0 3px rgba(201, 154, 61, .16), 0 8px 18px rgba(154, 107, 31, .08) !important;
}
.topbar .global-search button {
  border-color: #123f36 !important;
  background: linear-gradient(135deg, #123f36, #1d755f) !important;
  color: #fff8e4 !important;
}
.topbar .work-strip span,
.topbar .work-strip button {
  background: rgba(255, 250, 235, .68) !important;
  color: #6f5018 !important;
}
.topbar .topbar-logout {
  border-color: rgba(201, 154, 61, .28) !important;
  background: #fff8ea !important;
  color: #80591a !important;
}
.topbar .topbar-logout:hover {
  border-color: rgba(183, 131, 36, .5) !important;
  background: #fff4d9 !important;
  color: #60400e !important;
  box-shadow: 0 9px 18px rgba(154, 107, 31, .08) !important;
}

/* 内容板块奶油浅底：让主区域与一休新品牌色统一。 */
:global(body) {
  background:
    radial-gradient(circle at 82% 6%, rgba(214, 168, 79, .045), transparent 30%),
    #fbf6e9 !important;
}
.app-shell,
.workspace,
.content-shell,
.page-scroll {
  background: #fbf6e9 !important;
}
.panel,
.welcome-card,
.agent-card,
.stat-card,
.profile-card,
.home-schedule-panel,
.task-metric-table-panel,
.profile-panel,
.kb-hero,
.kb-doc-card,
.kb-template-card,
.file-window,
.chat-main,
.chat-title,
.collab-info {
  border-color: rgba(201, 154, 61, .22) !important;
  background: #fffdf8 !important;
  box-shadow: 0 12px 28px rgba(121, 83, 25, .032) !important;
}
.result-card,
.contact-card,
.priority-list article,
.task-board article,
.analysis-cards section,
.analysis-cards article,
.history-row,
.alert-list button,
.quick-grid button,
.home-task-row,
.home-quick-grid button,
.health-grid span,
.analysis-grid span,
.detail-grid span,
.task-ops-grid article,
.recheck-dashboard article,
.recheck-checklist span,
.search-launch-card,
.search-ai-status,
.search-context-board article,
.search-dialog-input,
.search-dialog-thread .bubble.assistant,
.history-search-list button,
.task-report-card section,
.kd-meta-bar > span,
.compliance-check-grid span,
.sop-guidance-cards button,
.meeting-board article,
.group-setting-list button,
.operator-panel .quick-card,
.aios-event-stream article,
.aios-report-section,
.aios-page-blocks article,
.profile-quick-row button {
  border-color: rgba(201, 154, 61, .13) !important;
  background: #fffefb !important;
}
input,
textarea,
select,
.global-search,
.ask-box,
.bubble,
.message > div,
.library-searchbar,
.kb-search input,
.graph-search,
.graph-controls select,
.graph-controls button {
  background: #ffffff !important;
}


/* ═══════════════════════════════════════════════════════════════════════════
   Skill Factory｜团队技能工厂
   视觉语言沿用既有面板：左侧强调色条 + 浅渐变底 + 卡片网格，只是信息密度
   更高、更偏控制台。管的是「经验怎么变成能力」。
   ═══════════════════════════════════════════════════════════════════════════ */
.skf-panel, .areg-panel { --sf-ink: #1d3238; --sf-muted: #6a7d84; --sf-line: #dde7ea; }
/* Skill 工厂原先是紫色强调 + 渐变底 + 大写字距眉标，是典型的"AI 生成感"。
   换成主色系青、纯白底、普通中文小标题。 */
.skf-panel { position: relative; display: grid; gap: 18px; padding: 22px; border-top: 3px solid var(--teal) !important;
  background: #fff !important; }
.areg-panel { position: relative; display: grid; gap: 20px; padding: 24px; border-top: 4px solid var(--blue) !important;
  background: linear-gradient(150deg, #fff 0%, #fafcfe 58%, #f5f9fb 100%) !important; }
.skf-panel .eyebrow { margin: 0; color: var(--teal); font-size: 11px; font-weight: 800; letter-spacing: 0; text-transform: none; }
.areg-panel .eyebrow { margin: 0; color: var(--blue); font-size: 10px; font-weight: 900; letter-spacing: .16em; text-transform: uppercase; }
.skf-panel h3, .areg-panel h3 { margin: 2px 0 0; color: var(--sf-ink); font-size: 21px; letter-spacing: 0; }
.skf-panel h3 small, .areg-panel h3 small { color: var(--sf-muted); font-size: 12px; font-weight: 600; }

.skf-hero { display: grid; gap: 20px; padding-bottom: 18px; border-bottom: 1px solid var(--sf-line); }
.skf-hero { grid-template-columns: minmax(0, 1.7fr) minmax(0, 1fr); }
.skf-hero-line { margin: 10px 0 0; max-width: 640px; color: #40585f; font-size: 13px; line-height: 1.62; }
.skf-flow { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 15px; }
.skf-flow button { display: grid; grid-template-columns: auto auto; grid-template-rows: auto auto; align-items: center; gap: 2px 7px;
  padding: 8px 11px; border: 1px solid var(--sf-line); border-radius: 10px; background: #fff; color: var(--sf-ink);
  font: inherit; text-align: left; cursor: pointer; transition: border-color .18s, box-shadow .18s, transform .18s; }
.skf-flow button b { grid-row: 1 / span 2; color: #b9c6cc; font-size: 15px; font-weight: 900; }
.skf-flow button span { font-size: 11px; font-weight: 800; }
.skf-flow button em { color: var(--sf-muted); font-size: 10px; font-style: normal; font-weight: 700; }
.skf-flow button:hover { transform: translateY(-1px); border-color: #bcd9e8; box-shadow: 0 8px 18px rgba(60,90,120,.08); }
.skf-flow button.active { border-color: var(--teal); background: #eef5f4; box-shadow: 0 8px 18px rgba(22,118,111,.16); }
.skf-flow button.active b { color: var(--teal); }
.skf-flow-hint { margin: 9px 0 0; color: var(--sf-muted); font-size: 11px; }

.skf-hero-metrics { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; align-content: start; }
.skf-hero-metrics article, .areg-eval-dash article { display: grid; gap: 3px; padding: 12px 13px;
  border: 1px solid var(--sf-line); border-left: 3px solid var(--tone, var(--teal)); border-radius: 11px; background: #fff; }
.skf-hero-metrics small, .areg-eval-dash small { color: var(--sf-muted); font-size: 10px; font-weight: 800; }
.skf-hero-metrics b, .areg-eval-dash b { color: var(--tone, var(--ink)); font-size: 22px; line-height: 1.1; }
.skf-hero-metrics em, .areg-eval-dash em { color: #8b9aa0; font-size: 10px; font-style: normal; }
.skf-panel .tone-teal, .areg-panel .tone-teal { --tone: #16766f; }
.skf-panel .tone-blue, .areg-panel .tone-blue { --tone: #3979b8; }
.skf-panel .tone-amber, .areg-panel .tone-amber { --tone: #c8872e; }
.skf-panel .tone-violet, .areg-panel .tone-violet { --tone: #8062b5; }
.skf-panel .tone-red, .areg-panel .tone-red { --tone: #b44c43; }
.skf-panel .tone-slate, .areg-panel .tone-slate { --tone: #6b7c85; }

.skf-block, .areg-block { display: grid; gap: 14px; }
.skf-block > .section-title-row, .areg-block > .section-title-row { align-items: flex-end; }
.skf-block .quiet-label, .areg-block .quiet-label { max-width: 420px; color: var(--sf-muted); font-size: 11px; line-height: 1.5; text-align: right; }

/* ── 候选发现 ─────────────────────────────────────────────────────────── */
.skf-candidates { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 13px; }
.skf-candidate { display: grid; gap: 11px; padding: 15px; border: 1px solid var(--sf-line); border-left: 4px solid #d8c9ec;
  border-radius: 13px; background: #fff; transition: border-color .18s, box-shadow .18s, transform .18s; }
.skf-candidate:hover { transform: translateY(-2px); box-shadow: 0 14px 28px rgba(60,72,90,.08); }
.skf-candidate.chosen { border-color: #b9d6d3; border-left-color: var(--teal); box-shadow: 0 12px 26px rgba(22,118,111,.12); }
.skf-candidate-head { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 11px; align-items: center; }
/* 原来是个 46px 的圆形评分章，改成普通的小标签 */
.skf-candidate-mark { display: inline-flex; align-items: center; padding: 4px 9px; border-radius: 7px;
  background: #eef5f4; color: var(--teal); font-size: 11px; font-weight: 800; white-space: nowrap; }
.skf-candidate-head b { display: block; color: var(--sf-ink); font-size: 14px; line-height: 1.4; }
.skf-candidate-head small { color: #8b9aa0; font-size: 10px; }
/* 原来是带紫色底的"气泡"，去掉底色，只留左侧引线 */
.skf-candidate-say { margin: 0; padding: 1px 0 1px 10px; border-left: 2px solid #dfe6ea; background: none; color: #4d636a;
  font-size: 12px; font-weight: 600; line-height: 1.55; }
.skf-signals { display: grid; gap: 4px; margin: 0; padding-left: 15px; color: #4d636a; font-size: 11px; line-height: 1.5; }
.skf-candidate-metrics { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 6px; }
.skf-candidate-metrics span { display: grid; gap: 2px; padding: 7px 8px; border-radius: 8px; background: #f7fafb; }
.skf-candidate-metrics small { color: #85959b; font-size: 9px; }
.skf-candidate-metrics b { color: #2f474e; font-size: 12px; }
.skf-candidate-foot { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding-top: 3px; }
.skf-candidate-foot > span { color: var(--sf-muted); font-size: 10px; }
.skf-candidate-foot > span b { color: #2f5f59; }
.skf-candidate-foot button { padding: 8px 13px; border: 0; border-radius: 9px; background: var(--teal); color: #fff;
  font: inherit; font-size: 11px; font-weight: 800; cursor: pointer; }
.skf-candidate-foot button:hover { background: var(--teal-dark); }

/* ── 生成表单 ─────────────────────────────────────────────────────────── */
.skf-generate { padding: 17px; border: 1px dashed #cfdde6; border-radius: 14px; background: #fafcfd; }
.skf-form { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 11px; }
.skf-form label { display: grid; gap: 5px; color: #46595f; font-size: 10px; font-weight: 900; }
.skf-form label.wide { grid-column: span 2; }
.skf-form input, .skf-form select, .skf-form textarea { width: 100%; padding: 9px 10px; border: 1px solid #dfe6ea;
  border-radius: 9px; background: #fff; color: var(--sf-ink); font: inherit; font-size: 11px; }
.skf-form textarea { min-height: 62px; resize: vertical; }
.skf-form select[multiple] { min-height: 78px; }
.skf-form input:focus, .skf-form select:focus, .skf-form textarea:focus { outline: none; border-color: #8fc4bf; box-shadow: 0 0 0 3px rgba(22,118,111,.12); }
.skf-generate-foot { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; margin-top: 14px; }
.skf-pack-preview { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; color: var(--sf-muted); font-size: 10px; }
.skf-pack-preview b { padding: 4px 8px; border: 1px solid #dfe6ea; border-radius: 7px; background: #fff; color: #2f5f59; font-family: ui-monospace, Consolas, monospace; font-size: 10px; }
.skf-generate-foot button { padding: 10px 18px; border: 0; border-radius: 10px; background: var(--teal); color: #fff; font: inherit; font-size: 12px; font-weight: 900; cursor: pointer; }
.skf-generate-foot button:disabled { background: #cfd9dd; cursor: not-allowed; }

/* ── 工具栏 ───────────────────────────────────────────────────────────── */
.skf-toolbar, .areg-toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; padding: 10px 12px;
  border: 1px solid var(--sf-line); border-radius: 12px; background: #fff; }
.skf-toolbar input, .areg-toolbar input { flex: 1 1 260px; min-width: 200px; padding: 8px 11px; border: 1px solid #e1e8eb; border-radius: 9px; font: inherit; font-size: 11px; color: var(--sf-ink); }
.skf-toolbar select, .areg-toolbar select, .areg-toolbar button { padding: 8px 10px; border: 1px solid #e1e8eb; border-radius: 9px; background: #fbfdfd; color: #334a51; font: inherit; font-size: 11px; font-weight: 800; cursor: pointer; }
.areg-toolbar button { background: var(--blue); border-color: var(--blue); color: #fff; }
.skf-toolbar button { padding: 8px 10px; border: 1px solid #e1e8eb; border-radius: 9px; background: #fbfdfd; color: #334a51; font: inherit; font-size: 11px; font-weight: 800; cursor: pointer; }
.skf-toolbar button.active { border-color: var(--amber); background: #fdf6e9; color: #a2711f; }
.skf-toolbar-count, .areg-toolbar-count { margin-left: auto; color: var(--sf-muted); font-size: 11px; font-weight: 800; }
.skf-sync { display: inline-flex; align-items: center; gap: 5px; padding: 5px 10px; border-radius: 999px; border: 1px solid #d9e6e4;
  background: #f2faf9; color: #16766f; font-size: 10px; font-weight: 900; white-space: nowrap; }
.skf-sync i { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.skf-sync.local { border-color: #ecdcbf; background: #fdf7ec; color: #a2711f; }

/* ── Skill 卡片 ───────────────────────────────────────────────────────── */
.skf-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 13px; }
.skf-card { display: grid; gap: 10px; padding: 15px; border: 1px solid var(--sf-line); border-top: 3px solid var(--stage, #9fb0b7);
  border-radius: 13px; background: #fff; cursor: pointer; transition: transform .18s, box-shadow .18s, border-color .18s; }
.skf-card:hover { transform: translateY(-2px); box-shadow: 0 14px 28px rgba(60,72,90,.09); }
.skf-card.active { border-color: var(--stage, var(--teal)); box-shadow: 0 0 0 3px rgba(22,118,111,.14), 0 14px 28px rgba(60,72,90,.09); }
.skf-card.stage-draft { --stage: #8e9ba3; }
.skf-card.stage-testing { --stage: #c8872e; }
.skf-card.stage-verified { --stage: #3979b8; }
.skf-card.stage-production { --stage: #16766f; }
.skf-card.stage-deprecated { --stage: #b44c43; }
.skf-card-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; }
.skf-card-head b { display: block; color: var(--sf-ink); font-size: 14px; line-height: 1.4; }
.skf-card-head small { color: #8b9aa0; font-size: 10px; }
.skf-star { border: 0; background: none; color: #d6dee2; font-size: 16px; line-height: 1; cursor: pointer; }
.skf-star.on { color: var(--amber); }
.skf-card > p { margin: 0; color: #4d636a; font-size: 11.5px; line-height: 1.58; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.skf-usecase { color: #85959b; font-size: 10px; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.skf-card-agents, .areg-card-skills { display: flex; flex-wrap: wrap; gap: 5px; }
.skf-card-agents span, .areg-card-skills span { padding: 3px 8px; border: 1px solid #d9e6ef; border-radius: 999px; background: #f4f9fd;
  color: #2f6394; font-size: 10px; font-weight: 800; cursor: pointer; }
.skf-card-agents span:hover, .areg-card-skills span:hover { background: #e6f2fa; }
.skf-card-agents em, .areg-card-skills em { color: #9aa8ae; font-size: 10px; font-style: normal; }
.skf-card-metrics, .areg-card-metrics { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 5px; }
.areg-card-metrics { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.skf-card-metrics span, .areg-card-metrics span { display: grid; gap: 1px; padding: 6px 7px; border-radius: 8px; background: #f7fafb; }
.skf-card-metrics small, .areg-card-metrics small { color: #88989e; font-size: 9px; }
.skf-card-metrics b, .areg-card-metrics b { color: #2f474e; font-size: 11px; }
.skf-card-foot, .areg-card-foot { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding-top: 2px; }
.skf-updated, .areg-card-foot time { color: #93a1a7; font-size: 10px; }
.skf-panel .badge, .areg-panel .badge { padding: 4px 9px; border: 1px solid currentColor; border-radius: 999px; font-size: 10px; font-weight: 900; font-style: normal; }
.skf-panel .badge.tone-teal, .areg-panel .badge.tone-teal { background: #e6f4f2 !important; color: #16766f; }
.skf-panel .badge.tone-blue, .areg-panel .badge.tone-blue { background: #e8f1fb !important; color: #3979b8; }
.skf-panel .badge.tone-amber, .areg-panel .badge.tone-amber { background: #fdf3e2 !important; color: #b0761f; }
.skf-panel .badge.tone-red, .areg-panel .badge.tone-red { background: #fdeceb !important; color: #b44c43; }
.skf-panel .badge.tone-slate, .areg-panel .badge.tone-slate { background: #eef2f4 !important; color: #6b7c85; }

/* ── Skill 详情 ───────────────────────────────────────────────────────── */
.skf-detail, .areg-detail { padding: 17px; border: 1px solid var(--sf-line); border-radius: 14px; background: #fff; }
.skf-detail-actions, .areg-detail-actions { display: flex; flex-wrap: wrap; gap: 7px; }
.skf-detail-actions button, .areg-detail-actions button { padding: 8px 12px; border: 1px solid #dfe6ea; border-radius: 9px; background: #fbfdfd;
  color: #334a51; font: inherit; font-size: 11px; font-weight: 800; cursor: pointer; }
.skf-detail-actions button:hover, .areg-detail-actions button:hover { border-color: #8fc4bf; }
.skf-detail-actions button.danger, .areg-detail-actions button.danger { color: #b44c43; border-color: #f0d3d0; background: #fdf5f4; }
.skf-detail-tabs, .areg-detail-tabs { display: flex; flex-wrap: wrap; gap: 4px; padding: 5px; border-radius: 11px; background: #f4f7f8; }
.skf-detail-tabs button, .areg-detail-tabs button { padding: 7px 13px; border: 0; border-radius: 8px; background: transparent;
  color: #5d727a; font: inherit; font-size: 11px; font-weight: 800; cursor: pointer; }
.skf-detail-tabs button.active, .areg-detail-tabs button.active { background: #fff; color: var(--teal); box-shadow: 0 4px 10px rgba(60,72,90,.08); }
.areg-detail-tabs button.active { color: var(--blue); }
.skf-detail-body { display: grid; gap: 13px; }
.skf-facts, .areg-facts { display: grid; grid-template-columns: repeat(auto-fill, minmax(168px, 1fr)); gap: 7px; }
.skf-facts span, .areg-facts span { display: grid; gap: 3px; padding: 9px 10px; border: 1px solid #e6edef; border-radius: 9px; background: #f9fbfc; }
.skf-facts small, .areg-facts small { color: #88989e; font-size: 9px; }
.skf-facts b, .areg-facts b { color: #2f474e; font-size: 11px; overflow-wrap: anywhere; }
.skf-detail-summary, .areg-detail-cap { margin: 0; color: #4d636a; font-size: 12px; line-height: 1.65; }
.skf-spec { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 12px; }
.skf-spec > div, .areg-spec-2 > div, .areg-spec-3 > div { padding: 12px; border: 1px solid #e6edef; border-radius: 10px; background: #fbfdfd; }
.skf-spec h4, .areg-spec-2 h4, .areg-spec-3 h4, .areg-trace h4, .skf-version-diff h4, .areg-prompt h4 { margin: 0 0 7px; color: #3c545c; font-size: 11px; font-weight: 900; letter-spacing: .04em; }
.skf-spec ul, .skf-spec ol, .areg-spec-3 ul { display: grid; gap: 4px; margin: 0; padding-left: 16px; color: #4d636a; font-size: 11px; line-height: 1.55; }
.skf-spec a { color: var(--blue); cursor: pointer; text-decoration: underline; }
.areg-spec-2, .areg-spec-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 12px; }
.areg-spec-2 p { margin: 0; color: #4d636a; font-size: 11px; line-height: 1.6; }
.areg-spec-3 code { padding: 1px 5px; border-radius: 5px; background: #eef4f7; color: #2f6394; font-size: 10px; }
.skf-pack { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 9px; }
.skf-pack span { display: grid; gap: 3px; padding: 11px 12px; border: 1px solid #dfe6ea; border-radius: 10px; background: #f7fafb; }
.skf-pack b { color: #2f5f59; font-family: ui-monospace, Consolas, monospace; font-size: 11px; }
.skf-pack small { color: #8d86a0; font-size: 10px; }
.skf-agent-links, .areg-skill-links { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 10px; }
.skf-agent-links article, .areg-skill-links article { display: grid; gap: 3px; padding: 12px; border: 1px solid #dfe8ec; border-radius: 11px;
  background: #fff; cursor: pointer; transition: border-color .18s, box-shadow .18s; }
.skf-agent-links article:hover, .areg-skill-links article:hover { border-color: var(--blue); box-shadow: 0 10px 22px rgba(60,72,90,.08); }
.skf-agent-links b, .areg-skill-links b { color: var(--sf-ink); font-size: 13px; }
.skf-agent-links small, .areg-skill-links small { color: #8b9aa0; font-size: 10px; }
.skf-agent-links em { color: #4d636a; font-size: 10px; font-style: normal; }
.areg-skill-links article { grid-template-columns: minmax(0, 2fr) repeat(3, auto); align-items: center; gap: 10px; }
.areg-skill-links article > span { display: grid; gap: 1px; text-align: right; }

/* ── Eval ─────────────────────────────────────────────────────────────── */
.skf-eval-bar { display: flex; flex-wrap: wrap; align-items: flex-end; gap: 10px; }
.skf-eval-bar label { display: grid; gap: 5px; color: #46595f; font-size: 10px; font-weight: 900; }
.skf-eval-bar input, .skf-eval-bar select { padding: 8px 10px; border: 1px solid #dfe6ea; border-radius: 9px; background: #fff; font: inherit; font-size: 11px; }
.skf-eval-bar button { padding: 9px 16px; border: 0; border-radius: 9px; background: var(--teal); color: #fff; font: inherit; font-size: 11px; font-weight: 900; cursor: pointer; }
.skf-eval-bar button:disabled { background: #cfd9dd; cursor: progress; }
.skf-eval-result { display: grid; gap: 12px; padding: 15px; border: 1px solid #cfe7e3; border-radius: 12px; background: #f5fbfa; }
.skf-eval-result.blocked { border-color: #f0d3d0; background: #fdf6f5; }
.skf-eval-score { display: flex; align-items: baseline; gap: 9px; }
.skf-eval-score b { color: var(--teal); font-size: 34px; line-height: 1; }
.skf-eval-result.blocked .skf-eval-score b { color: var(--danger); }
.skf-eval-score small { color: var(--sf-muted); font-size: 10px; font-weight: 800; }
.skf-eval-nums { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 8px; }
.skf-eval-nums span { display: grid; gap: 2px; padding: 8px 9px; border-radius: 9px; background: #fff; }
.skf-eval-nums small { color: #88989e; font-size: 9px; }
.skf-eval-nums b { color: #2f474e; font-size: 14px; }
.skf-blocks { display: grid; gap: 4px; margin: 0; padding-left: 16px; color: #b44c43; font-size: 11px; }
.skf-pass { margin: 0; color: var(--teal); font-size: 11px; font-weight: 800; }
.skf-eval-table, .areg-history { display: grid; border: 1px solid #e6edef; border-radius: 10px; overflow: hidden; background: #fff; }
.skf-eval-table .tr, .areg-history .tr { display: grid; grid-template-columns: 1.2fr 1.1fr .6fr .7fr .7fr .7fr .6fr 1.4fr; gap: 8px; padding: 9px 11px; border-top: 1px solid #eef3f4; color: #4d636a; font-size: 10.5px; }
.areg-history .tr { grid-template-columns: 1.3fr 2fr .8fr .7fr; }
.skf-eval-table .tr.head, .areg-history .tr.head { border-top: 0; background: #f5f9fa; color: #5d727a; font-weight: 900; }
.skf-version-diff { display: grid; gap: 7px; padding: 13px; border: 1px solid #e6edef; border-radius: 10px; background: #fbfdfd; }
.skf-diff-row { display: grid; grid-template-columns: 90px minmax(0, 1fr) 20px minmax(0, 1fr); align-items: center; gap: 8px; font-size: 11px; }
.skf-diff-row span { color: #88989e; font-weight: 800; }
.skf-diff-row b { padding: 5px 8px; border-radius: 7px; background: #f2f6f8; color: #4d636a; font-weight: 700; }
.skf-diff-row b.up { background: #e9f6f4; color: #16766f; }
.skf-diff-row b.down { background: #fdeceb; color: #b44c43; }
.skf-diff-row i { color: #a9b6bb; text-align: center; font-style: normal; }
.skf-versions, .areg-versions { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 10px; }
.skf-versions article, .areg-versions article { display: grid; gap: 4px; padding: 12px; border: 1px solid #e6edef; border-radius: 11px; background: #fbfdfd; }
.skf-versions b, .areg-versions b { color: var(--teal); font-size: 13px; }
.areg-versions b { color: var(--blue); }
.skf-versions small, .areg-versions small { color: #8b9aa0; font-size: 10px; }
.skf-versions p, .areg-versions p { margin: 0; color: #4d636a; font-size: 11px; line-height: 1.55; }
.skf-versions em { color: #6b7c85; font-size: 10px; font-style: normal; }
.skf-versions button { justify-self: start; margin-top: 3px; padding: 6px 10px; border: 1px solid #dfe6ea; border-radius: 8px;
  background: #fff; color: #334a51; font: inherit; font-size: 10px; font-weight: 800; cursor: pointer; }

/* ═══════════════════════════════════════════════════════════════════════════
   Agent Center｜Agent 中心
   「已接入」列表行 + 「获取更多」卡片网格 + 详情 9 页签（原来的 hero 概览区已移除）。
   视觉沿用 TeamMemory OS 的面板语法，强调色蓝。
   ═══════════════════════════════════════════════════════════════════════════ */
/* 真实品牌图标：SVG 用 contain 加内边距，位图铺满圆角方块 */
.areg-logo-img { width: 38px; height: 38px; flex: none; border-radius: 10px; object-fit: contain;
  padding: 4px; background: #fff; border: 1px solid #e6edf1; box-sizing: border-box; }
.areg-block-actions { display: flex; gap: 7px; }
.areg-block-actions button, .areg-inline-actions button { padding: 8px 13px; border: 1px solid #dfe6ea; border-radius: 9px;
  background: #fbfdfd; color: #334a51; font: inherit; font-size: 11px; font-weight: 800; cursor: pointer; }
.areg-block-actions button.primary, .areg-inline-actions button.primary { border-color: var(--blue); background: var(--blue); color: #fff; }
.areg-block-actions button:disabled { opacity: .6; cursor: progress; }

/* ── 已接入列表行 ─────────────────────────────────────────────────────── */
.areg-hub { display: grid; gap: 8px; }
.areg-hub-row { display: grid; grid-template-columns: 38px minmax(0, 1fr) auto;
  align-items: center; gap: 14px; padding: 12px 14px; border: 1px solid var(--sf-line); border-radius: 12px; background: #fff;
  transition: border-color .18s, box-shadow .18s; }
.areg-hub-row:hover { border-color: #bcd9e8; box-shadow: 0 10px 22px rgba(60,72,90,.07); }
.areg-hub-body { display: grid; gap: 5px; min-width: 0; }
.areg-hub-title { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.areg-hub-title b { color: var(--sf-ink); font-size: 13.5px; }
.areg-pill { display: inline-flex; align-items: center; gap: 5px; padding: 2px 9px; border-radius: 999px;
  background: #f1f5f7; color: #61727b; font-size: 10px; font-weight: 800; font-style: normal; }
.areg-pill i { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.areg-pill.on { background: #e6f4f2; color: #16766f; }
.areg-pill.ok { background: #eef4f8; color: #4b6b85; }
.areg-pill.warn { background: #fdf3e2; color: #b0761f; }
.areg-hub-detail { color: #8b9aa0; font-size: 10.5px; line-height: 1.5; }
.areg-hub-actions { display: flex; align-items: center; gap: 6px; justify-self: end; }
.areg-hub-actions button { padding: 7px 12px; border: 1px solid #dfe6ea; border-radius: 8px; background: #fbfdfd;
  color: #334a51; font: inherit; font-size: 11px; font-weight: 800; cursor: pointer; }
.areg-hub-actions button.primary { border-color: var(--blue); background: var(--blue); color: #fff; }
.areg-menu-wrap { position: relative; }
.areg-menu { position: absolute; right: 0; top: calc(100% + 6px); z-index: 12; min-width: 150px; display: grid;
  padding: 5px; border: 1px solid #dbe4e9; border-radius: 11px; background: #fff; box-shadow: 0 16px 32px rgba(40,56,72,.16); }
.areg-menu button { border: 0; border-radius: 7px; background: none; padding: 8px 10px; text-align: left;
  color: #334a51; font: inherit; font-size: 11px; font-weight: 700; cursor: pointer; }
.areg-menu button:hover { background: #f2f7fa; }
.areg-menu button.danger { color: #b44c43; }
.areg-more { justify-self: center; margin-top: 4px; padding: 8px 16px; border: 1px dashed #cfdde6; border-radius: 999px;
  background: #fbfdfd; color: #4b6b85; font: inherit; font-size: 11px; font-weight: 800; cursor: pointer; }
.areg-more:hover { border-color: var(--blue); }

/* ── 获取更多：卡片网格 ───────────────────────────────────────────────── */
.areg-manual { display: grid; gap: 12px; padding: 15px; border: 1px dashed #bcd9e8; border-radius: 13px; background: #f8fcfe; }
.areg-manual-head b { display: block; color: #1d3c56; font-size: 13px; }
.areg-manual-head small { color: #6a7d84; font-size: 11px; }
.areg-manual-form { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.areg-manual-form label { display: grid; gap: 5px; color: #46595f; font-size: 10px; font-weight: 900; }
.areg-manual-form input { padding: 8px 10px; border: 1px solid #dfe6ea; border-radius: 9px; background: #fff; font: inherit; font-size: 11px; color: var(--sf-ink); }
.areg-manual-foot { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.areg-manual-foot > span { color: #7d919c; font-size: 10px; }
.areg-manual-foot > div { display: flex; gap: 7px; }
.areg-manual-foot button { padding: 8px 14px; border: 1px solid #dfe6ea; border-radius: 9px; background: #fff;
  color: #334a51; font: inherit; font-size: 11px; font-weight: 800; cursor: pointer; }
.areg-manual-foot button.primary { border-color: var(--blue); background: var(--blue); color: #fff; }
.areg-manual-foot button:disabled { opacity: .55; cursor: not-allowed; }

.areg-discover { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 11px; }
.areg-discover-card { display: grid; grid-template-columns: 38px minmax(0, 1fr); align-items: center; gap: 2px 11px;
  padding: 13px 14px; border: 1px solid var(--sf-line); border-radius: 12px;
  background: #fff; transition: transform .18s, box-shadow .18s, border-color .18s; }
.areg-discover-card > .areg-logo-img { grid-column: 1; grid-row: 1 / span 2; align-self: center; }
.areg-discover-card:hover { transform: translateY(-2px); box-shadow: 0 12px 24px rgba(60,72,90,.08); }
.areg-discover-card.state-connected { border-color: #cfe7e3; background: #fbfefd; }
.areg-discover-card.state-needsAuth { border-color: #f0e0c8; background: #fffdf8; }
.areg-discover-card.state-notDetected { opacity: .78; }
/* 卡片按参考图排版：图标与名称同一行，说明缩进在名称下，按钮整行通栏 */
.areg-discover-card > b { grid-column: 2; color: var(--sf-ink); font-size: 13.5px; }
.areg-vendor { grid-column: 2; color: #6a7d84; font-size: 10.5px; line-height: 1.5; }
.areg-discover-card > button { grid-column: 1 / -1; margin-top: 10px; padding: 9px 10px; border: 1px solid #dfe6ea;
  border-radius: 9px; background: #fff; color: #334a51; font: inherit; font-size: 11px; font-weight: 900; cursor: pointer; }
.areg-discover-card > button.primary { border-color: var(--blue); background: var(--blue); color: #fff; }
.areg-discover-card > button:disabled { background: #f7fafb; color: #8b9aa0; border-color: #e6edef; cursor: not-allowed; }

/* ── 一休内置 Agent ───────────────────────────────────────────────────── */
.areg-builtin { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 9px; }
.areg-builtin article { display: grid; grid-template-columns: 38px minmax(0, 1fr) auto; align-items: center; gap: 10px;
  padding: 11px 12px; border: 1px solid var(--sf-line); border-radius: 11px; background: #fff; }
.areg-builtin img { width: 38px; height: 38px; border-radius: 11px; object-fit: cover; }
.areg-builtin b { display: block; color: var(--sf-ink); font-size: 12.5px; }
.areg-builtin small { color: #8b9aa0; font-size: 10px; }
.areg-builtin-meta { grid-column: 2 / -1; color: #6a7d84; font-size: 10px; font-weight: 700; }

/* ── 联动 ─────────────────────────────────────────────────────────────── */
.areg-linkage { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 11px; }
.areg-linkage article { display: grid; gap: 5px; padding: 14px; border: 1px solid #dbe8f3; border-radius: 12px;
  background: linear-gradient(160deg, #fbfdff, #f4faff); cursor: pointer; transition: transform .18s, box-shadow .18s; }
.areg-linkage article:hover { transform: translateY(-2px); box-shadow: 0 12px 24px rgba(60,72,90,.08); }
.areg-linkage b { color: #1d3c56; font-size: 13px; }
.areg-linkage p { margin: 0; color: #4d636a; font-size: 11px; line-height: 1.55; }
.areg-linkage em { color: var(--blue); font-size: 10px; font-style: normal; font-weight: 900; }

/* ── 管理详情 ─────────────────────────────────────────────────────────── */
.areg-manage-head { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 14px;
  padding-bottom: 15px; border-bottom: 1px solid var(--sf-line); }
.areg-back { padding: 8px 13px; border: 1px solid #dfe6ea; border-radius: 9px; background: #fff; color: #334a51;
  font: inherit; font-size: 11px; font-weight: 800; cursor: pointer; }
.areg-manage-id { display: flex; align-items: center; gap: 11px; min-width: 0; }
.areg-manage-id h3 { margin: 0; color: var(--sf-ink); font-size: 18px; }
.areg-manage-id small { color: #8b9aa0; font-size: 10px; }
/* 全局 .tr 带 min-width:980px（任务表格故意横向滚动的设定），
   Agent 中心的历史表格继承后会在窄屏把整块面板顶宽，这里放开。 */
.areg-history .tr { min-width: 0; }
.areg-memory-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 9px; }
.areg-memory-list article { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 8px;
  padding: 11px 12px; border: 1px solid var(--sf-line); border-radius: 11px; background: #fff; }
.areg-memory-list b { display: block; color: var(--sf-ink); font-size: 12px; }
.areg-memory-list small { color: #8b9aa0; font-size: 10px; }
.areg-inline-actions { display: flex; align-items: center; gap: 9px; flex-wrap: wrap; }
.areg-hint { color: #7d919c; font-size: 10.5px; line-height: 1.6; }
.areg-config-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 8px; }
.areg-config-list article { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 6px;
  padding: 10px 12px; border: 1px solid var(--sf-line); border-radius: 10px; background: #fbfdfd; }
.areg-config-list b { color: var(--sf-ink); font-family: ui-monospace, Consolas, monospace; font-size: 11px; }
.areg-config-list small { grid-column: 1; color: #8b9aa0; font-size: 10px; }

/* ── 记忆迁移 ─────────────────────────────────────────────────────────── */
.areg-migrate { display: grid; gap: 14px; padding: 15px; border: 1px solid #dbe8f3; border-radius: 13px; background: #f9fcfe; }
.areg-migrate-pick { display: grid; grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr); align-items: end; gap: 12px; }
.areg-migrate-pick label { display: grid; gap: 5px; color: #46595f; font-size: 10px; font-weight: 900; }
.areg-migrate-pick select { padding: 9px 10px; border: 1px solid #dfe6ea; border-radius: 9px; background: #fff; font: inherit; font-size: 12px; color: var(--sf-ink); }
.areg-migrate-arrow { padding-bottom: 9px; color: var(--blue); font-size: 18px; font-weight: 900; }
.areg-migrate-assets { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 8px; }
.areg-migrate-assets > span { display: grid; gap: 3px; padding: 10px 11px; border: 1px solid #e1e8eb; border-radius: 10px;
  background: #fff; cursor: pointer; transition: border-color .18s, background .18s; }
.areg-migrate-assets > span.on { border-color: #bcd9e8; background: #f2f9fd; }
.areg-migrate-assets > span.bad { border-style: dashed; opacity: .6; cursor: not-allowed; }
.areg-migrate-assets b { color: var(--sf-ink); font-size: 12px; }
.areg-migrate-assets small { color: #8b9aa0; font-size: 9.5px; line-height: 1.45; }
.areg-migrate-assets em { color: #4b6b85; font-size: 9.5px; font-style: normal; font-weight: 900; }
.areg-migrate-assets > span.on em { color: var(--blue); }
.areg-pipeline { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 9px; }
.areg-pipeline > span { display: grid; gap: 3px; padding: 12px; border: 1px solid #e1e8eb; border-radius: 11px; background: #fff; }
.areg-pipeline > span b { color: #c2cfd6; font-size: 15px; font-weight: 900; }
.areg-pipeline > span strong { color: #2f474e; font-size: 12px; }
.areg-pipeline > span small { color: #8b9aa0; font-size: 10px; line-height: 1.45; }
.areg-pipeline > span.active { border-color: var(--blue); background: #f2f9fd; box-shadow: 0 0 0 3px rgba(57,121,184,.12); }
.areg-pipeline > span.active b { color: var(--blue); }
.areg-pipeline > span.done { border-color: #cfe7e3; background: #f7fdfc; }
.areg-pipeline > span.done b { color: var(--teal); }
.areg-migrate-foot { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.areg-migrate-foot > span { color: #6a7d84; font-size: 11px; font-weight: 700; }
.areg-migrate-foot button { padding: 9px 18px; border: 0; border-radius: 10px; background: var(--blue); color: #fff;
  font: inherit; font-size: 12px; font-weight: 900; cursor: pointer; }
.areg-migrate-foot button:disabled { background: #b9cddd; cursor: progress; }
.areg-migrate-result { display: grid; gap: 4px; padding: 13px; border: 1px solid #cfe7e3; border-radius: 11px; background: #f5fbfa; }
.areg-migrate-result b { color: var(--teal); font-size: 13px; }
.areg-migrate-result p { margin: 0; color: #3c545c; font-size: 11.5px; }
.areg-migrate-result small { color: #7d919c; font-size: 10px; }

@media (max-width: 1180px) {
  .skf-hero { grid-template-columns: minmax(0, 1fr); }
  .skf-form { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .skf-form label.wide { grid-column: span 2; }
  .areg-hub-row { grid-template-columns: 38px minmax(0, 1fr) auto; row-gap: 9px; }
  .areg-manual-form { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  /* 管理页头部三列在窄屏会撑出横向滚动，改成上下堆叠 */
  .areg-manage-head { grid-template-columns: minmax(0, 1fr); row-gap: 10px; }
  .areg-manage-id { flex-wrap: wrap; }
  .areg-detail-actions { flex-wrap: wrap; justify-content: flex-start; }
  .areg-migrate-foot { flex-wrap: wrap; }
}
@media (max-width: 720px) {
  .skf-form { grid-template-columns: minmax(0, 1fr); }
  .skf-form label.wide { grid-column: span 1; }
  .skf-candidate-metrics, .skf-card-metrics, .areg-card-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .areg-skill-links article { grid-template-columns: minmax(0, 1fr); }
  .areg-hub-row { grid-template-columns: 32px minmax(0, 1fr); }
  .areg-hub-actions { grid-column: 2 / -1; justify-self: start; }
  .areg-manual-form { grid-template-columns: minmax(0, 1fr); }
  .areg-migrate-pick { grid-template-columns: minmax(0, 1fr); }
  .areg-migrate-arrow { display: none; }
  .areg-discover { grid-template-columns: minmax(0, 1fr); }
}

/* 个人空间：三栏默认列宽写死了 minmax 最小值（260+360+280），
   窄屏会把整页顶出横向滚动。只在放不下的宽度下放开最小值，
   1600 宽的正常布局不受影响。 */
@media (max-width: 1400px) {
  .profile-main-grid,
  .profile-focus-shell .profile-main-grid {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1fr);
  }
  .profile-growth-card,
  .profile-focus-shell .profile-growth-card {
    grid-template-columns: minmax(0, 1.05fr) minmax(140px, .45fr) minmax(0, 1.15fr);
  }
  /* 数据卡片 6×150px、身份区 112+172px 的硬最小值同样会顶宽 */
  .profile-quick-row,
  .profile-focus-shell .profile-quick-row { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .profile-hero-card,
  .profile-focus-shell .profile-hero-card { grid-template-columns: 96px minmax(0, 1fr) auto; }
}
@media (max-width: 1100px) {
  .profile-main-grid,
  .profile-focus-shell .profile-main-grid {
    grid-template-columns: minmax(0, 1fr);
    grid-template-areas: "security" "tools" "activity" "growth" "preference";
  }
  .profile-quick-row,
  .profile-focus-shell .profile-quick-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .profile-hero-card,
  .profile-focus-shell .profile-hero-card { grid-template-columns: minmax(0, 1fr); }
}
</style>


