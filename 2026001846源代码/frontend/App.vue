<template>
  <main class="app-shell" :class="{ collapsed: navCollapsed, 'auth-shell': !isAuthenticated }">
    <section v-if="!isAuthenticated" class="auth-gate">
      <div class="auth-visual">
        <div class="auth-grid" aria-hidden="true"></div>
        <div class="auth-brand">
          <img src="/static/yixiu-logo-full.png" alt="一修" />
          <span>设备检修知识检索与作业系统</span>
        </div>
        <div class="auth-intro">
          <p>面向工业现场的智能检修工作台</p>
          <h1>让每一次检修<br />都有依据、有流程、有沉淀</h1>
          <div class="auth-capabilities">
            <span><b>01</b>多模态故障检索</span>
            <span><b>02</b>标准化作业指导</span>
            <span><b>03</b>检修知识沉淀</span>
          </div>
        </div>
        <p class="auth-footnote">一修 · 智能设备检修知识服务平台</p>
      </div>
      <div class="auth-form-side">
        <form class="auth-card" @submit.prevent="authMode === 'login' ? login() : register()">
          <div class="auth-card-head">
            <p>{{ authMode === 'login' ? '欢迎回来' : '创建工作账号' }}</p>
            <h2>{{ authMode === 'login' ? '登录一修工作台' : '加入一修协作平台' }}</h2>
            <span>{{ authMode === 'login' ? '登录后进入设备检修综合工作台' : '完善基础信息后即可开始协同检修' }}</span>
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
    <div v-if="showSplash" ref="bootScreenRef" class="boot-screen" aria-label="一修系统开屏动画">
      <div class="boot-grid" aria-hidden="true"></div>
      <div class="boot-flow flow-a" aria-hidden="true"></div>
      <div class="boot-flow flow-b" aria-hidden="true"></div>
      <section ref="bootMarkRef" class="boot-mark">
        <img ref="bootLogoRef" src="/static/yixiu-logo-full.png" alt="一修" />
      </section>
    </div>
    <aside class="side-nav">
      <img
        ref="brandLogoRef"
        class="brand"
        :src="navCollapsed ? '/static/yixiu-logo-icon.png' : '/static/yixiu-logo-full.png'"
        alt="一修"
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
          <p class="breadcrumb">一修 / {{ currentNav.label }}</p>
          <h1>{{ currentNav.title }}</h1>
        </div>
        <div v-else class="task-chamber-wrap">
          <button class="task-chamber" type="button" :class="{ open: taskChamberOpen }" @click="taskChamberOpen = !taskChamberOpen">
            <i></i>
          </button>
          <div v-if="taskChamberOpen" class="task-chamber-pop">
            <button type="button" @click="activePage = 'home'; globalSearchFocused = false; taskChamberOpen = false">
              <b>综合工作台</b><small>回到首页总览</small>
            </button>
            <button type="button" @click="activePage = 'tasks'; taskPanel = 'manage'; globalSearchFocused = false; taskChamberOpen = false">
              <b>待办 {{ overview.stats.pending }}</b><small>进入任务管理</small>
            </button>
            <button type="button" @click="activePage = 'tasks'; taskPanel = 'recheck'; globalSearchFocused = false; taskChamberOpen = false">
              <b>待复检 {{ overview.stats.review }}</b><small>查看复检验收</small>
            </button>
            <button class="danger" type="button" @click="activePage = 'tasks'; taskPanel = 'overview'; globalSearchFocused = false; taskChamberOpen = false">
              <b>高风险 {{ overview.stats.highRisk }}</b><small>定位重点风险</small>
            </button>
          </div>
        </div>
        <form class="global-search" @submit.prevent="runGlobalSearch" @focusin="globalSearchFocused = true">
          <span>
            <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="path in iconParts('search')" :key="path" :d="path"></path>
            </svg>
          </span>
          <input v-model="globalKeyword" placeholder="搜索工单、设备、资料、联系人" />
          <button type="submit" aria-label="全局搜索">搜索</button>
        </form>
        <div v-if="!globalSearchFocused" class="work-strip">
          <button type="button" @click="goTopbarTask('pending')">待办 {{ overview.stats.pending }}</button>
          <button type="button" @click="goTopbarTask('review')">待复检 {{ overview.stats.review }}</button>
          <button class="bad" type="button" @click="goTopbarTask('highRisk')">高风险 {{ overview.stats.highRisk }}</button>
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
      <section class="page-scroll" :class="`page-theme-${activePage}`">
        <section v-if="activePage === 'home'" class="page-grid">
          <div
            class="panel span-7 home-news-carousel"
            @mouseenter="pauseNewsCarousel"
            @mouseleave="resumeNewsCarousel"
          >
            <div class="news-carousel-stage">
              <a class="news-image-link" :href="activeNews.link" target="_blank" rel="noopener">
                <transition name="news-fade" mode="out-in">
                  <img :key="activeNews.image" :src="activeNews.image" :alt="activeNews.title" />
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
              <img src="/static/yixiu-logo-full.png" alt="一修系统 Logo" />
              <div>
                <p class="eyebrow">我的今日工作</p>
                <h2>{{ user.name }}，今天重点处理 {{ overview.stats.pending + overview.stats.inProgress + overview.stats.review }} 项检修工作</h2>
                <p>{{ nowText }}，{{ user.department }}。请优先确认高风险、即将逾期和待复检任务。</p>
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
              <div class="summary-metric"><b>{{ overview.stats.highRisk }}</b><span>高风险待确认</span></div>
              <div class="summary-metric"><b>{{ overview.stats.weekKnowledge }}</b><span>本周知识沉淀</span></div>
            </div>
            <div class="health-grid">
              <span>待接收：{{ overview.stats.pending }} 项</span>
              <span>进行中：{{ overview.stats.inProgress }} 项</span>
              <span>待复检：{{ overview.stats.review }} 项</span>
              <span>今日完成：{{ overview.stats.completed }} 项</span>
              <span>需确认：{{ overview.stats.highRisk }} 项高风险</span>
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
                <p class="eyebrow">今日任务摘要</p>
                <h3>需要处理的检修工单</h3>
              </div>
              <div class="task-title-actions"><span>{{ visibleTodayTasks.length }} 项任务</span><button class="ghost" type="button" @click="activePage = 'tasks'">查看全部 →</button></div>
            </div>
            <div class="home-task-list">
              <button v-for="(task, index) in visibleTodayTasks.slice(0, 4)" :key="task.id" class="home-task-row" :class="`risk-${task.severity}`" type="button" @click="openTask(task)">
                <span class="task-index-block">
                  <b>{{ String(index + 1).padStart(2, '0') }}</b>
                  <i></i>
                </span>
                <span class="task-device-block">
                  <small>{{ task.workOrderNo }}</small>
                  <b>{{ task.equipment_name }}</b>
                  <em>{{ task.equipment_no }} · {{ task.equipment_model }}</em>
                </span>
                <span class="task-fault-block">
                  <span><b>{{ task.fault_type }}</b><i :class="['badge', task.severity]">{{ severityText(task.severity) }}</i></span>
                  <small>{{ task.current_step }}</small>
                </span>
                <span class="task-owner-block">
                  <i>{{ task.assignee_name.slice(0, 1) }}</i>
                  <span><small>负责人</small><b>{{ task.assignee_name }}</b></span>
                </span>
                <span class="task-progress-block">
                  <span><b>{{ statusText(task.status) }}</b><em>{{ task.progress }}%</em></span>
                  <i><u :style="{ width: `${task.progress}%` }"></u></i>
                  <small>{{ task.current_step }}</small>
                </span>
                <span class="row-arrow">→</span>
              </button>
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
                <div class="chart-tile-head"><b>任务状态分布</b><small>按工单状态</small></div>
                <EChart :option="homeStatusOption" class="chart-canvas" height="250px" />
              </section>
              <section class="chart-tile">
                <div class="chart-tile-head"><b>风险等级占比</b><small>{{ overview.stats.highRisk }} 项高风险</small></div>
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
                <h2>观微｜智能检索 agent <span class="agent-online-dot"></span><small>在线</small></h2>
                <b>您的检索专家</b>
                <p>发现设备故障线索，解析故障机理、型号、图片和检修文档，助力快速定位与修复。</p>
              </div>
            </div>
            <div class="search-agent-tools">
              <button type="button" @click="searchPanel = 'multimodal'">
                <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12a8 8 0 0 1 13.7-5.6"></path><path d="M20 4v6h-6"></path><path d="M20 12a8 8 0 0 1-13.7 5.6"></path><path d="M4 20v-6h6"></path></svg>
                <span><b>多模态检索</b><small>图文语音深度检索</small></span>
              </button>
              <button type="button" @click="searchPanel = 'history'">
                <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 8v5l3 2"></path><path d="M3.05 11a9 9 0 1 1 2.64 6.36"></path><path d="M3 17v-6h6"></path></svg>
                <span><b>历史检索</b><small>查看历史记录</small></span>
              </button>
              <button type="button" @click="searchPanel = 'update'">
                <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h13"></path><path d="M4 12h10"></path><path d="M4 17h7"></path><path d="m16 15 2 2 4-5"></path></svg>
                <span><b>深度更新</b><small>知识持续迭代</small></span>
              </button>
            </div>
          </div>

          <template v-if="searchPanel === 'multimodal'">
            <div class="panel span-all search-input-panel search-fusion-panel" :class="{ 'is-collapsed': !searchMultimodalExpanded, 'is-expanded': searchMultimodalExpanded }">
              <div class="search-fusion-head">
                <div class="search-panel-heading">
                  <span class="search-step">01</span>
                  <div><p class="eyebrow">多模态检索</p><h3>输入线索，观微同步分析</h3><small>设备参数、故障现象、现场图片、文档和语音会合并成一次检索上下文。</small></div>
                </div>
                <div class="inline-actions">
                  <button type="button" class="ghost-toggle" @click="searchMultimodalExpanded = !searchMultimodalExpanded">
                    {{ searchMultimodalExpanded ? '收起' : '展开' }}
                    <svg class="ui-icon" :class="{ up: searchMultimodalExpanded }" viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"></path></svg>
                  </button>
                  <button type="button" @click="searchPanel = 'history'">历史</button>
                  <button type="button" @click="searchPanel = 'update'">沉淀</button>
                  <button type="button" @click="clearOperatorMessages">清空</button>
                  <button class="primary" type="button" :disabled="loading.search" @click="runSearch">{{ loading.search ? '研判中' : '生成研判' }}</button>
                </div>
              </div>

              <div v-show="!searchMultimodalExpanded" class="search-collapse-summary">
                <span><b>设备</b>{{ searchForm.deviceName || '未填写' }}</span>
                <span><b>型号</b>{{ searchForm.deviceModel || '未填写' }}</span>
                <span><b>故障</b>{{ searchForm.faultType }} / {{ searchForm.faultCode || '无故障码' }}</span>
                <span><b>证据</b>{{ searchFiles.length ? `${searchFiles.length} 个附件` : '未上传' }}</span>
                <button type="button" @click="runSearch">{{ loading.search ? '研判中' : '生成研判' }}</button>
              </div>

              <div v-show="searchMultimodalExpanded" class="search-fusion-body">
                <div class="search-fusion-input">
                  <div class="form-grid">
                    <label>设备名称<input v-model="searchForm.deviceName" placeholder="如：摩托车发动机总成" /></label>
                    <label>设备型号<input v-model="searchForm.deviceModel" placeholder="如：CG-125" /></label>
                    <label>故障代码<input v-model="searchForm.faultCode" placeholder="如：NOISE-02" /></label>
                    <label>设备类别<select v-model="searchForm.category"><option>发动机</option><option>电气系统</option><option>液压系统</option><option>点火系统</option></select></label>
                    <label>故障类型<select v-model="searchForm.faultType"><option>异响</option><option>过热</option><option>渗漏</option><option>点火故障</option></select></label>
                    <label>检修等级<select v-model="searchForm.maintenanceLevel"><option>一级巡检</option><option>二级检修</option><option>三级大修</option></select></label>
                    <label class="wide">故障现象<textarea v-model="searchForm.query" placeholder="描述现场现象、声音、报警、温度、图片观察结果"></textarea></label>
                  </div>

                  <div class="search-evidence-box">
                    <div class="upload-zone search-upload-zone" @dragover.prevent @drop.prevent="addDroppedFiles">
                      <input ref="searchFileInput" type="file" multiple accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.md,.mp4,.webm" @change="addFiles($event, 'search')" />
                      <span class="upload-mark"><svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 16V4M7.5 8.5 12 4l4.5 4.5M5 14v4a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-4"></path></svg></span>
                      <span class="upload-copy"><b>添加现场证据与检修资料</b><small>支持图片、视频、PDF、SOP、巡检记录</small></span>
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
                      <b>检索上下文</b>
                      <span>{{ searchForm.deviceName || '未填写设备' }} / {{ searchForm.deviceModel || '未填写型号' }}</span>
                      <small>{{ searchForm.faultType }} · {{ searchForm.maintenanceLevel }} · {{ searchForm.faultCode || '无故障码' }}</small>
                    </article>
                    <article>
                      <b>证据准备</b>
                      <span>{{ searchFiles.length ? `${searchFiles.length} 个附件已加入` : '等待现场资料' }}</span>
                      <small>{{ searchForm.query ? '故障描述已填写' : '建议补充故障现象、声音、温度或报警信息' }}</small>
                    </article>
                    <article>
                      <b>下一步建议</b>
                      <span>{{ searchResult ? '查看引用依据并转任务' : '先生成研判摘要' }}</span>
                      <small>{{ searchResult ? `${searchResult.confidence}% 置信度，可继续追溯` : '可上传图片、文档或使用语音补充线索' }}</small>
                    </article>
                  </div>

                </div>

                <div class="search-fusion-ai">
                  <div class="search-ai-status">
                    <img :src="operatorProfile.avatar" :alt="operatorProfile.name" @error="handleAvatarError" />
                    <div><b>观微正在协助</b><small>{{ searchResult ? `已匹配 ${searchResult.references.length} 份资料` : '等待现场线索' }}</small></div>
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
                      <div><b>检索摘要</b><p>{{ searchResult ? searchResult.phenomenonSummary : '填写设备和故障现象后，观微会整理匹配摘要。' }}</p></div>
                    </article>
                    <article>
                      <span><svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3a9 9 0 1 0 9 9"></path><path d="M12 7v5l3 2"></path></svg></span>
                      <div><b>初步判断</b><p>{{ searchResult ? searchResult.causes.slice(0, 2).join('；') : '暂无判断，建议先上传现场图片或维修文档。' }}</p></div>
                    </article>
                  </div>
                  <div class="search-dialog-thread">
                    <div class="bubble assistant">我是观微。你可以上传现场图片、补充语音描述，或直接问“下一步先检查哪里”。</div>
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
                <input v-model="operatorInput" placeholder="请输入您的问题、故障描述或补充信息..." />
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
                <div><p class="eyebrow">检索结果生成</p><h3>{{ searchResult ? '故障研判摘要' : '等待检索分析' }}</h3><small>{{ searchResult ? '综合文本、设备参数与现场线索形成判断' : '请先在多模态检索中启动检索' }}</small></div>
              </div>
              <template v-if="searchResult">
                <div class="analysis-summary"><span>研判结论</span><h3>{{ searchResult.phenomenonSummary }}</h3></div>
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
                <h4>可能原因</h4>
                <ul><li v-for="item in searchResult.causes" :key="item">{{ item }}</li></ul>
                <h4>推荐检查位置 / 工具</h4>
                <p>{{ searchResult.positions.join('、') }}；工具：{{ searchResult.tools.join('、') }}</p>
                <div class="card-actions"><button class="primary" type="button" @click="prepareKnowledgeFromSearch">沉淀为知识</button><button type="button" @click="searchPanel = 'multimodal'">重新检索</button></div>
              </template>
              <div v-else class="empty search-empty-state">
                <span class="analysis-orbit"><i></i><i></i><i></i><b>检</b></span>
                <h4>检索结果将在这里生成</h4>
                <p>系统会结合设备型号、故障现象和上传材料，给出风险、原因与检查建议。</p>
              </div>
            </div>

            <div class="panel search-results-panel">
              <div class="panel-head">
                <div>
                  <p class="eyebrow">03 · 结果分类</p>
                  <h3>维修手册、案例、SOP、安全规范与知识节点</h3>
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
              <div v-else class="result-filter-empty"><b>当前分类暂无匹配结果</b><span>可以切换到“全部”，或调整设备型号和故障描述后重新检索。</span><button type="button" @click="selectResultTab('全部')">查看全部结果</button></div>
            </div>

            <div class="panel span-all maintenance-advice-panel" v-if="searchResult">
              <div class="advice-heading"><div><p class="eyebrow">检修建议</p><h3>推荐作业路径</h3></div><span>{{ searchResult.suggestion.steps.length }} 个步骤</span></div>
              <div class="sop-list">
                <span v-for="(step, index) in searchResult.suggestion.steps" :key="step"><b>{{ index + 1 }}</b>{{ step }}</span>
              </div>
              <p class="advice-reference"><b>引用依据</b>{{ searchResult.references.slice(0, 3).map((item) => item.title).join('、') }}</p>
            </div>
          </template>

          <template v-else-if="searchPanel === 'history'">
            <div class="panel search-history-panel">
              <div class="panel-head"><div><p class="eyebrow">历史检索</p><h3>最近检索记录</h3><small>点击记录可回填检索条件，继续追溯同类问题。</small></div><button type="button" @click="searchPanel = 'multimodal'">新检索</button></div>
              <div class="history-command-strip">
                <button type="button" @click="toast('已筛出可复用的高置信度检索')"><b>高置信复用</b><small>优先使用 85% 以上记录</small></button>
                <button type="button" @click="toast('已按设备型号合并相似故障')"><b>相似故障合并</b><small>同型号、同现象自动归组</small></button>
                <button type="button" @click="toast('已生成历史检索追溯摘要')"><b>生成追溯摘要</b><small>用于检修任务备注</small></button>
              </div>
              <div class="history-stat-grid">
                <span><b>{{ searchHistory.length }}</b><small>近期检索</small></span>
                <span><b>{{ Math.round(searchHistory.reduce((sum, item) => sum + item.confidence, 0) / Math.max(searchHistory.length, 1)) }}%</b><small>平均置信度</small></span>
                <span><b>{{ new Set(searchHistory.map(item => item.faultType)).size }}</b><small>故障类型</small></span>
              </div>
              <div class="history-search-list">
                <button v-for="item in searchHistory" :key="item.id" type="button" @click="applySearchHistory(item)">
                  <span><b>{{ item.title }}</b><small>{{ item.time }} · {{ item.deviceName }} · {{ item.model }} · {{ item.faultType }}</small></span>
                  <em>{{ item.confidence }}%</em>
                </button>
              </div>
              <div class="history-action-row">
                <button type="button" @click="toast('已按故障类型整理历史检索')">按故障归类</button>
                <button type="button" @click="toast('已标记高匹配历史记录')">标记高匹配</button>
                <button type="button" @click="searchPanel = 'update'">沉淀为知识</button>
              </div>
            </div>
            <div class="panel history-learning-panel">
              <div class="panel-head"><div><p class="eyebrow">经验学习推荐</p><h3>基于历史检索的知识推荐</h3><small>按近期故障类型、资料引用与作业路径自动聚合。</small></div></div>
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

          <template v-else-if="searchPanel === 'update'">
            <div class="panel span-all search-update-panel">
              <div class="panel-head">
                <div><p class="eyebrow">沉淀更新</p><h3>把本次检索结论沉淀为知识</h3><small>用于沉淀检索到的有效原因、处置路径、复检结论和引用依据。</small></div>
                <button type="button" @click="prepareKnowledgeFromSearch">从当前检索生成</button>
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
                  <label>知识标题<input v-model="knowledgeForm.title" placeholder="如：发动机异响复检案例" /></label>
                  <label>资料类型<select v-model="knowledgeForm.type"><option>历史故障案例</option><option>维修手册</option><option>SOP</option><option>安全规范</option></select></label>
                  <label>适用设备<input v-model="knowledgeForm.equipment" /></label>
                  <label>设备型号<input v-model="knowledgeForm.model" /></label>
                  <label>来源依据<input v-model="knowledgeForm.source" placeholder="工单号、手册章节或现场记录" /></label>
                  <label>人工标签<input v-model="knowledgeForm.tagText" placeholder="使用逗号分隔，如：异响,气门,复测" /></label>
                  <label class="wide">沉淀摘要<textarea v-model="knowledgeForm.summary" placeholder="描述故障现象、原因、处理方式、复检结论和引用依据"></textarea></label>
                </div>
                <aside class="knowledge-update-aside">
                  <div class="update-quality-card">
                    <b>入库质量检查</b>
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
              <button class="primary" type="button" @click="saveKnowledge">提交知识审核</button>
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
        </section>

        <section v-else-if="activePage === 'tasks'" class="page-grid tasks-page">
          <div class="panel span-all task-nav-panel">
            <div class="panel-head">
              <div>
                <p class="eyebrow">检修任务</p>
                <h3>检修任务闭环中心</h3>
                <small>从任务接收、标准作业到复检验收与协作沟通</small>
              </div>
              <div class="tabs">
                <button v-for="tab in taskTabs" :key="tab.key" type="button" :class="{ active: taskPanel === tab.key }" @click="taskPanel = tab.key">{{ tab.label }}</button>
              </div>
            </div>
          </div>

          <template v-if="taskPanel === 'overview'">
            <div class="panel span-all task-metric-table-panel">
              <div class="section-title-row">
                <div><p class="eyebrow">作业入口</p><h3>今日检修协同工作台</h3></div>
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
                <div><p class="eyebrow">数据分析</p><h3>任务趋势、状态、风险、设备和人员负载</h3></div>
                <button type="button" @click="toast('已展开更多分析：平均检修时长、按时完成率、返工数量、高频故障设备')">查看更多分析</button>
              </div>
              <div class="analysis-cards">
                <section>
                  <div class="trend-card-head"><b>近 7 天任务趋势</b><span>累计 {{ taskTrendTotal }} 项</span></div>
                  <div class="trend-summary"><strong>{{ taskTrendData.at(-1) }}</strong><span>今日处理量</span><em :class="{ down: taskTrendChange < 0 }">{{ taskTrendChange >= 0 ? '↑' : '↓' }} {{ Math.abs(taskTrendChange) }} 较昨日</em></div>
                  <EChart :option="taskTrendOption" class="chart-canvas task-trend-echart" height="166px" />
                </section>
                <section class="chart-section">
                  <b>任务状态占比</b>
                  <EChart :option="taskStatusOption" class="chart-canvas" height="200px" click-field="key" @click="filterTaskBy('status', $event)" />
                  <p class="chart-hint">点击柱条可按状态筛选</p>
                </section>
                <section class="chart-section">
                  <b>风险等级分布</b>
                  <EChart :option="taskRiskOption" class="chart-canvas" height="200px" click-field="key" @click="filterTaskBy('severity', $event)" />
                  <p class="chart-hint">点击扇区可按风险筛选</p>
                </section>
                <section>
                  <b>设备类型与故障排行</b>
                  <button v-for="item in taskCategoryAnalysis" :key="item.key" type="button" class="chip-row" @click="filterTaskBy('category', item.key)">{{ item.label }} <em>{{ item.count }}</em></button>
                  <button v-for="item in faultRankAnalysis" :key="item.key" type="button" class="chip-row warm" @click="filterTaskBy('faultType', item.key)">{{ item.label }} <em>{{ item.count }}</em></button>
                </section>
              </div>
            </div>
            <div class="panel span-all priority-panel">
              <p class="eyebrow">重点任务</p>
              <div class="priority-list">
                <article v-for="task in priorityTasks" :key="task.id">
                  <header class="priority-task-top">
                    <div><small>{{ task.workOrderNo }}</small><b>{{ task.equipment_name }}</b></div>
                    <span><i :class="['badge', task.severity]">{{ severityText(task.severity) }}</i><em>{{ statusText(task.status) }}</em></span>
                  </header>
                  <p class="priority-task-desc">{{ task.description }}</p>
                  <div class="priority-task-meta">
                    <span><small>设备编号</small><b>{{ task.equipment_no }}</b></span>
                    <span><small>负责人</small><b>{{ task.assignee_name }}</b></span>
                    <span><small>协作人员</small><b>{{ task.collaborators?.join('、') || '待分配' }}</b></span>
                  </div>
                  <div class="priority-task-progress">
                    <div><span :style="{ width: `${task.progress}%` }"></span></div>
                    <b>{{ task.progress }}%</b>
                  </div>
                  <footer><span><small>当前步骤</small><b>{{ task.current_step }}</b><em>剩余 {{ remainingTime(task) }}</em></span><button type="button" @click="openTask(task)">查看详情 <i>→</i></button></footer>
                </article>
              </div>
            </div>
            <div class="panel span-all task-event-panel">
              <div class="task-event-heading"><div><p class="eyebrow">任务动态</p><h3>现场进展与节点记录</h3></div><span>{{ taskEvents.length }} 条记录</span></div>
              <div class="timeline task-events"><article v-for="event in taskEvents" :key="event.id"><i></i><time>{{ event.time }}</time><p>{{ event.text }}</p></article></div>
            </div>
          </template>

          <template v-if="taskPanel === 'manage'">
            <div class="panel span-all task-manage-panel">
              <div class="filters">
                <select v-model="taskFilters.status"><option value="all">全部关系</option><option value="pending">待处理</option><option value="in_progress">检修中</option><option value="review">待复检</option><option value="completed">已完成</option></select>
                <select v-model="taskFilters.severity"><option value="all">全部关系</option><option value="low">低</option><option value="medium">中</option><option value="high">高</option></select>
                <select v-model="taskFilters.category"><option value="all">全部关系</option><option v-for="item in taskCategoryAnalysis" :key="item.key" :value="item.key">{{ item.label }}</option></select>
                <select v-model="taskFilters.faultType"><option value="all">全部关系</option><option v-for="item in faultRankAnalysis" :key="item.key" :value="item.key">{{ item.label }}</option></select>
                <input v-model="taskFilters.keyword" placeholder="搜索设备/负责人/型号/协作人员" />
                <div class="view-switch"><button type="button" :class="{ active: taskView === 'table' }" @click="taskView = 'table'">表格</button><button type="button" :class="{ active: taskView === 'board' }" @click="taskView = 'board'">看板</button></div>
                <button class="primary" type="button" @click="showTaskForm = true">新建检修任务</button>
              </div>
              <div class="sop-guidance-strip">
                <section>
                  <p class="eyebrow">标准化作业指引</p>
                  <h3>按设备类型与检修等级推送流程</h3>
                  <small>当前筛选下自动匹配 SOP、工具证据和合规校验项。</small>
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
                <div class="tr head"><span>工单</span><span>设备</span><span>故障描述</span><span>风险</span><span>负责人</span><span>步骤</span><span>状态</span><span>操作</span></div>
                <div v-for="task in filteredTasks" :key="task.id" class="tr">
                  <span>{{ task.workOrderNo }}</span>
                  <span>{{ task.equipment_name }}<small>{{ task.equipment_model }}</small></span>
                  <span>{{ task.description }}</span>
                  <span><i :class="['badge', task.severity]">{{ severityText(task.severity) }}</i></span>
                  <span>{{ task.assignee_name }}</span>
                  <span>{{ task.current_step }} · {{ task.progress }}%</span>
                  <span>{{ statusText(task.status) }}</span>
                  <span class="inline-actions task-row-actions">
                    <button class="task-row-action detail" type="button" @click="openTask(task)"><span>查看</span><b>详情</b></button>
                    <button class="task-row-action flow" type="button" :disabled="task.status === 'completed'" @click="handleTaskPrimary(task)"><span>{{ task.status === 'review' ? '进入' : '任务' }}</span><b>{{ task.status === 'review' ? '复检' : '流转' }}</b></button>
                  </span>
                </div>
              </div>
              <div v-else class="task-board">
                <section v-for="column in taskBoardColumns" :key="column.key">
                  <h4>{{ column.label }} <small>{{ column.tasks.length }}</small></h4>
                  <article v-for="task in column.tasks" :key="task.id" @click="openTask(task)">
                    <b>{{ task.equipment_name }}</b>
                    <small>{{ task.workOrderNo }} · {{ task.fault_type }}</small>
                    <span><i :class="['badge', task.severity]">{{ severityText(task.severity) }}</i>{{ task.progress }}%</span>
                  </article>
                </section>
              </div>
            </div>
          </template>

          <template v-if="taskPanel === 'recheck'">
            <div class="panel span-all recheck-panel">
              <div class="recheck-heading"><div><p class="eyebrow">复检评估</p><h3>质量验收与闭环确认</h3></div><span>{{ recheckTasks.length }} 项待核查</span></div>
              <div class="recheck-dashboard">
                <article v-for="item in recheckDashboard" :key="item.label" :class="`tone-${item.tone}`">
                  <span>
                    <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path v-for="path in iconParts(item.icon)" :key="path" :d="path"></path></svg>
                  </span>
                  <div><small>{{ item.label }}</small><b>{{ item.value }}</b><em>{{ item.hint }}</em></div>
                </article>
              </div>              <div class="recheck-grid">
                <article v-for="task in recheckTasks" :key="task.id" class="result-card recheck-card" :class="{ warning: recheckForms[task.id].result !== '通过' }">
                  <div class="recheck-card-head">
                    <span class="recheck-mark" aria-hidden="true">
                      <svg class="ui-icon" viewBox="0 0 24 24"><path v-for="path in iconParts('check')" :key="path" :d="path"></path></svg>
                    </span>
                    <div><b>{{ task.title }}</b><small>{{ task.equipment_name }} · {{ task.current_step }}</small></div>
                    <strong>{{ task.progress }}%</strong>
                  </div>
                  <div class="recheck-meta">
                    <span><small>工单编号</small><b>{{ task.workOrderNo }}</b></span>
                    <span><small>负责人</small><b>{{ task.assignee_name }}</b></span>
                    <span><small>当前状态</small><b>{{ statusText(task.status) }}</b></span>
                  </div>
                                    <div class="recheck-checklist">
                    <span v-for="item in recheckChecklist(task)" :key="item.label" :class="{ ok: item.ok }">
                      <i>
                        <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path v-for="path in iconParts(item.ok ? 'check' : 'alert')" :key="path" :d="path"></path></svg>
                      </i>
                      <b>{{ item.label }}</b>
                      <small>{{ item.desc }}</small>
                    </span>
                  </div>                  <label class="recheck-field">
                    <span>验收结论</span>
                    <div class="recheck-select-wrap">
                      <select v-model="recheckForms[task.id].result"><option>通过</option><option>限期整改</option><option>返工</option><option>不通过</option></select>
                    </div>
                  </label>
                  <label class="recheck-field">
                    <span>复检记录</span>
                    <textarea v-model.trim="recheckForms[task.id].comment" placeholder="填写复测数据、安全检查结果和复检意见"></textarea>
                  </label>
                  <div class="recheck-card-footer">
                    <span><i></i>{{ recheckForms[task.id].comment ? '复检信息已填写' : '请核对数据后保存' }}</span>
                    <button class="primary" type="button" @click="saveRecheck(task)">保存复检结果</button>
                  </div>
                </article>
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
                <p class="eyebrow">知识库</p>
                <h3>检修知识资产中心</h3>
                <small>连接知识网络、文件、技术资料与经验沉淀</small>
              </div>
              <div class="tabs">
                <button v-for="tab in knowledgeTabs" :key="tab.key" type="button" :class="{ active: knowledgePanel === tab.key }" @click="knowledgePanel = tab.key">{{ tab.label }}</button>
              </div>
            </div>
          </div>

          <div v-if="knowledgePanel === 'network'" class="panel span-all graph-panel graph-console-panel">
            <div class="graph-toolbar">
              <div class="graph-toolbar-main">
                <label class="graph-search expanded">
                  <button class="graph-search-trigger" type="button" @click.prevent="openGraphSearch" aria-label="展开知识搜索">
                    <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true">
                      <path v-for="path in iconParts('search')" :key="path" :d="path"></path>
                    </svg>
                  </button>
                  <input ref="graphSearchInput" v-model="knowledgeKeyword" placeholder="搜索汽车、摩托、设备、故障或资料" @focus="graphSearchExpanded = true" @keyup.enter="loadKnowledge" />
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
                  <div class="graph-filter-head"><b>图谱筛选</b><button type="button" @click="graphKindFilter = 'all'; graphRelationFilter = 'all'; graphLegendFiltered = {}">清空</button></div>
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
                  <label><span>知识注释</span><input v-model="graphShowLabels" type="checkbox" /></label>
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
                    <small class="node-type-pill">{{ graphKindMeta[selectedGraphNode.kind]?.text || '知识实体' }}</small>
                    <p>{{ selectedGraphNode.summary }}</p>
                    <div class="tag-line">
                      <span v-for="tag in selectedGraphNode.tags" :key="tag">{{ tag }}</span>
                    </div>
                    <button class="primary" type="button" @click="openKnowledge(selectedGraphNode.source)">查看完整资料</button>
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
                <div v-else class="empty">点击图谱节点查看关联资料、任务和检修建议。</div>
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
                <h3>关联文档</h3>
                <button v-for="item in selectedGraphDocuments" :key="item.id" type="button" @click="openKnowledge(item)">
                  <span>{{ item.title }}</span><em>{{ item.updated_at || item.type || '已入库' }}</em>
                </button>
                <p v-if="!selectedGraphDocuments.length" class="map-doc-empty">点击图谱节点后，这里会显示对应资料。</p>
              </aside>
              </div>
            </div>
          </div>

          <div v-if="knowledgePanel === 'files'" class="panel span-all file-manager">
            <div class="file-toolbar">
              <div>
                <p class="eyebrow">文件管理器</p>
                <h3>维修资料、现场图片、SOP、报告与版本文件</h3>
              </div>
              <input ref="fileManagerInput" type="file" multiple @change="addFiles($event, 'manager')" />
              <div class="file-actions">
                <button class="file-tool-btn" type="button" title="新建文件夹" @click="createFileFolder()">
                  <span>＋</span><b>文件夹</b>
                </button>
                <button class="file-tool-btn" type="button" title="重命名当前目录" @click="renameActiveFolder()">
                  <span>✎</span><b>重命名</b>
                </button>
                <button class="file-tool-btn primary" type="button" title="上传资料" @click="$refs.fileManagerInput.click()">
                  <span>↑</span><b>上传</b>
                </button>
              </div>
            </div>
            <div class="file-window">
              <aside class="file-sidebar">
                <div class="file-tree-hint">拖动文件到目录可调整分级</div>
                <div class="file-tree-list">
                  <div
                    v-for="node in fileTreeItems"
                    :key="node.id"
                    role="button"
                    tabindex="0"
                    :class="{ active: activeFolder === node.name, child: node.level > 0, collapsed: node.hasChildren && !node.expanded, dropover: fileDropTarget === node.name }"
                    class="file-tree-row"
                    :style="{ '--level': node.level }"
                    draggable="true"
                    @click="selectFileFolder(node)"
                    @keydown.enter.prevent="selectFileFolder(node)"
                    @dragstart="startFolderDrag(node)"
                    @dragover.prevent="fileDropTarget = node.name"
                    @dragleave="fileDropTarget = ''"
                    @drop.prevent="dropFileOnFolder(node)"
                  >
                    <i>{{ node.hasChildren ? (node.expanded ? '▾' : '▸') : '' }}</i>
                    <span>{{ node.name }}</span>
                    <em v-if="node.count">{{ node.count }}</em>
                    <small class="file-node-actions">
                      <button type="button" title="新增子文件夹" @click.stop="createFileFolder(node.name)">＋</button>
                      <button type="button" title="重命名目录" @click.stop="renameFileFolder(node.name)">✎</button>
                    </small>
                  </div>
                </div>
              </aside>
              <section class="file-desktop" @dragover.prevent @drop.prevent="addManagerDroppedFiles">
                <div class="file-pathbar">
                  <span>一修资料盘 / {{ activeFolder }}</span>
                  <input v-model="fileKeyword" placeholder="搜索文件名称、设备、型号" />
                  <select v-model="fileType"><option value="all">全部关系</option><option>PDF</option><option>Word</option><option>图片</option><option>视频</option><option>其他</option></select>
                  <button type="button" @click="fileView = fileView === 'table' ? 'card' : 'table'">{{ fileView === 'table' ? '图标视图' : '详细信息' }}</button>
                </div>
                <div v-if="filteredFiles.length === 0" class="empty">这里还没有匹配文件，可以拖拽文件到此处或点击上传资料。</div>
                <div v-else-if="fileView === 'card'" class="desktop-grid">
                  <button v-for="file in filteredFiles" :key="file.id" class="desktop-file" :class="{ selected: selectedFileRow === file.id }" type="button" draggable="true" @dragstart="startFileDrag(file)" @dblclick="previewFile(file)" @click="selectedFileRow = file.id">
                    <span class="file-icon" :class="fileIconClass(file)">{{ fileIcon(file) }}</span>
                    <b>{{ file.name }}</b>
                    <small>{{ file.type }} · {{ file.size }}</small>
                    <i>{{ file.parseStatus }}</i>
                  </button>
                </div>
                <div v-else class="table file-table">
                  <div class="tr head"><span>文件</span><span>分类</span><span>设备</span><span>上传</span><span>审核</span><span>解析</span><span>版本</span><span>操作</span></div>
                  <div v-for="file in filteredFiles" :key="file.id" class="tr" draggable="true" @dragstart="startFileDrag(file)">
                    <span>{{ file.name }}<small>{{ file.type }} · {{ file.size }}</small></span>
                    <span>{{ file.category }}</span>
                    <span>{{ file.equipment }} / {{ file.model }}</span>
                    <span>{{ file.uploader }}<small>{{ file.uploaded_at }}</small></span>
                    <span>{{ file.auditStatus }}</span>
                    <span>{{ file.parseStatus }}</span>
                    <span>{{ file.version }}</span>
                    <span class="inline-actions"><button type="button" @click="previewFile(file)">预览</button><button type="button" @click="toast('已收藏')">收藏</button></span>
                  </div>
                </div>
                <div class="file-statusbar">
                  <span>{{ filteredFiles.length }} 个项目</span>
                  <span>双击文件可预览，支持图片、PDF、视频和文本本地预览</span>
                </div>
              </section>
            </div>
          </div>

          <div v-if="knowledgePanel === 'library'" class="panel span-all knowledge-library-panel">
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
                  <div class="kb-template-icon">{{ tpl.icon }}</div>
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
                <article v-for="tpl in availableTemplates" :key="'lib-' + tpl.id" class="kb-template-card">
                  <div class="kb-template-icon">{{ tpl.icon }}</div>
                  <div class="kb-template-info">
                    <h4>{{ tpl.name }}</h4>
                    <span>{{ tpl.category }}</span>
                    <p>{{ tpl.description }}</p>
                  </div>
                  <button class="kb-template-use" type="button" @click="createDocFromTemplate(tpl)">使用 →</button>
                </article>
              </div>
            </article>
          </div>

          <div v-if="knowledgePanel === 'update'" class="panel span-all">
            <p class="eyebrow">沉淀更新</p>
            <div class="form-grid">
              <label>知识标题<input v-model="knowledgeForm.title" placeholder="如：发动机异响复检案例" /></label>
              <label>资料类型<select v-model="knowledgeForm.type"><option>历史故障案例</option><option>维修手册</option><option>SOP</option><option>安全规范</option></select></label>
              <label>适用设备<input v-model="knowledgeForm.equipment" /></label>
              <label>设备型号<input v-model="knowledgeForm.model" /></label>
              <label>来源依据<input v-model="knowledgeForm.source" placeholder="工单号、手册章节或现场记录" /></label>
              <label>人工标签<input v-model="knowledgeForm.tagText" placeholder="使用逗号分隔，如：异响,气门,复测" /></label>
              <label class="wide">沉淀摘要<textarea v-model="knowledgeForm.summary" placeholder="描述故障现象、原因、处理方式、复检结论和引用依据"></textarea></label>
            </div>
            <button class="primary" type="button" @click="saveKnowledge">提交知识审核</button>
            <div class="knowledge-review-list">
              <article v-for="item in pendingKnowledge" :key="item.id" class="result-card">
                <div><b>{{ item.title }}</b><small>{{ item.equipment }} / {{ item.model }} · {{ knowledgeStatusText(item.status) }}</small><p>{{ item.summary }}</p></div>
                <label>人工修正<textarea v-model="knowledgeCorrections[item.id]" placeholder="核对并修正模型整理结果；无误可直接通过"></textarea></label>
                <div class="tag-line"><span v-for="tag in item.tags || []" :key="tag">{{ tag }}</span></div>
                <div class="card-actions"><button class="primary" type="button" @click="reviewKnowledge(item, 'approved')">审核入库</button><button type="button" @click="reviewKnowledge(item, 'rejected')">退回修改</button></div>
              </article>
            </div>
          </div>
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
                <span class="profile-skill-badge">高级检修员</span>
              </div>
              <p>工号：{{ user.employeeId }} · {{ user.department }} · {{ user.role }}</p>
              <div class="profile-progress">
                <span>资料完整度</span>
                <i><b style="width: 86%"></b></i>
                <em>86%</em>
              </div>
              <small>完善检修档案、擅长设备和资质信息，可提升任务分派准确度。</small>
              <div class="profile-tags-soft">
                <span v-for="tag in user.specialties" :key="tag">{{ tag }}</span>
                <span>{{ user.skillLevel }}</span>
              </div>
            </div>
            <div class="profile-hero-actions">
              <button type="button" @click="openProfileEditor">
                <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20h9"></path><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"></path></svg>
                编辑资料
              </button>
              <button type="button" @click="activePage = 'tasks'; taskPanel = 'manage'">
                <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3v3M17 3v3M4 9h16M6 5h12a2 2 0 0 1 2 2v12H4V7a2 2 0 0 1 2-2Z"></path></svg>
                查看任务
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
                <p>能力值 / 检修画像</p>
                <h3>{{ profileGrowthScore }}</h3>
                <span>本月完成率稳定，复检通过率保持优秀。</span>
                <i><b style="width: 78%"></b></i>
              </div>
              <div class="profile-growth-level">
                <small>当前等级</small>
                <b>{{ user.skillLevel }}</b>
                <button type="button" @click="activePage = 'profile'">成长中心</button>
              </div>
              <div class="profile-growth-benefits">
                <span v-for="item in profileGrowthBenefits" :key="item.title">
                  <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path v-for="path in iconParts(item.icon)" :key="path" :d="path"></path></svg>
                  {{ item.title }}
                </span>
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

          <div v-if="false" class="page-grid profile-page profile-workspace">
          <div class="profile-hero span-all profile-identity-card">
            <img :src="user.avatar" alt="" @error="handleAvatarError" />
            <div>
              <p class="eyebrow">个人身份卡</p>
              <h2>{{ user.name }}</h2>
              <p>{{ user.role }} · {{ user.department }} · 工号 {{ user.employeeId }}</p>
              <div class="tag-line">
                <span v-for="tag in user.specialties" :key="tag">{{ tag }}</span><span>技能等级：{{ user.skillLevel }}</span>
              </div>
            </div>
            <div class="identity-summary">
              <span><small>当前状态</small><b>{{ user.status || '在岗' }}</b></span>
              <span><small>本月任务</small><b>{{ myTasks.length }}</b></span>
              <button class="primary" type="button" @click="openProfileEditor">编辑资料</button>
            </div>
          </div>

          <article v-for="section in profileSections" :key="section.key" class="profile-section" :class="[section.span, `profile-${section.key}`]">
            <div class="panel-head">
              <span class="profile-section-icon">
                <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true">
                  <path v-for="path in iconParts(section.icon)" :key="path" :d="path"></path>
                </svg>
              </span>
              <div>
                <p class="eyebrow">{{ section.group }}</p>
                <h3>{{ section.title }}</h3>
              </div>
              <button v-if="section.action" type="button" @click="runProfileAction(section)">{{ section.action }}</button>
            </div>
            <div class="profile-metrics" v-if="section.metrics">
              <span v-for="metric in section.metrics" :key="metric.label"><b>{{ metric.value }}</b>{{ metric.label }}</span>
            </div>
            <div class="profile-list">
              <button v-for="item in section.items" :key="item.title" type="button" @click="runProfileItem(item)">
                <span class="profile-item-icon">
                  <svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true">
                    <path v-for="path in iconParts(item.icon || section.icon)" :key="path" :d="path"></path>
                  </svg>
                </span>
                <span class="profile-item-copy">
                  <b>{{ item.title }}</b>
                  <small>{{ item.desc }}</small>
                </span>
                <em v-if="item.meta">{{ item.meta }}</em>
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
          <img class="operator-avatar" :src="operatorProfile.avatar" :alt="operatorProfile.name" @error="handleAvatarError" />
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
                <span class="trace-tag" :class="step.type">{{ stepLabel(step.type) }}</span>
                <span v-if="step.tool" class="trace-tool">{{ step.tool }}</span>
                <span class="trace-text">{{ step.content || traceResult(step) }}</span>
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
          <div><p class="eyebrow">任务详情与作业执行</p><h2>{{ selectedTask.title }}</h2><small>{{ selectedTask.workOrderNo }} · {{ selectedTask.equipment_name }} / {{ selectedTask.equipment_model }}</small></div>
          <span><i :class="['badge', selectedTask.severity]">{{ severityText(selectedTask.severity) }}</i><b>{{ statusText(selectedTask.status) }}</b></span>
        </header>
        <div class="task-modal-progress"><div><span :style="{ width: `${selectedTask.progress}%` }"></span></div><b>{{ selectedTask.progress }}%</b></div>
        <div class="detail-grid task-modal-stats">
          <span><small>设备编号</small><b>{{ selectedTask.equipment_no }}</b></span>
          <span><small>负责人</small><b>{{ selectedTask.assignee_name }}</b></span>
          <span><small>当前步骤</small><b>{{ selectedTask.current_step }}</b></span>
          <span><small>剩余时间</small><b>{{ remainingTime(selectedTask) }}</b></span>
        </div>
        <p class="task-modal-description">{{ selectedTask.description }}</p>
        <div class="personalized-sop-panel">
          <div>
            <p class="eyebrow">个性化流程推送</p>
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
        <div class="task-modal-section-title"><span>标准作业步骤</span><small>{{ selectedTask.sop?.length || 0 }} 个步骤</small></div>
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
            <span v-if="taskLinkedKnowledge.length === 0" class="tl-go-kb" @click.stop="activePage = 'knowledge'; knowledgePanel = 'library'; selectedTask = null">去知识库关联 →</span>
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
          <img v-if="selectedFile.type === '图片' && selectedFile.url" :src="selectedFile.url" alt="" />
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
              <span><small>来源</small><b>{{ selectedKnowledge.source || '一修知识库' }}</b></span>
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
          <label class="wide">参与人员<input v-model.trim="scheduleDraft.people" maxlength="80" placeholder="负责人：聪明的一修" /></label>
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
            <img src="/static/agents/tiangong.png" alt="天工" @error="handleAgentAvatarError" />
            <i></i>
          </span>
          <div>
            <small>{{ tgRunUi.statusText }}</small>
            <b>{{ tgRunUi.title }}</b>
          </div>
          <em>{{ tgRunUi.current }}/{{ tgRunUi.total }}</em>
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
import { createOverviewFromMock, mockAgents, mockUser } from './src/data/yixiuMock.js'
import EChart from './src/components/EChart.vue'

const navItems = [
  { key: 'home', label: '首页', title: '综合工作台', icon: 'dashboard' },
  { key: 'search', label: '智能检索', title: '多模态故障分析', icon: 'search' },
  { key: 'tasks', label: '检修任务', title: '工单与复检闭环', icon: 'wrench' },
  { key: 'knowledge', label: '知识库', title: '资料、文件与知识网络', icon: 'network' },
  { key: 'profile', label: '个人中心', title: '人员、记录与核查', icon: 'user' }
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
const newsSlides = [
  {
    title: '2026中工智库沙龙第六期：提质向新 绿智赋能体系跃升',
    summary: '围绕工业体系提质升级、绿色制造与智能化赋能，探讨制造业高质量发展的新路径。',
    source: '中国工业新闻网',
    date: '2026-07-15',
    link: 'https://www.cinn.cn/xyx/2026/07-15/K18x4jQ1.html',
    image: 'https://oss.cinn.cn/media/image/20260715/012e9b875c444656af0a945a58026e7eb9.jpg@2XJW693dA_1WtavmcvmULHD_OJ5beEBtA0fnygW-cBQ@rs:fill:720:0@g:sm@q:75@.webp?width=4000&height=2250'
  },
  {
    title: '工业绿色转型持续推进，智能制造成为提质增效关键抓手',
    summary: '从设备更新、工艺优化到数字化管理，绿色低碳与智能运维正在重塑工业生产组织方式。',
    source: '中国工业新闻网',
    date: '专题图集',
    link: 'https://www.cinn.cn/xyx/2026/07-15/K18x4jQ1.html',
    image: 'https://oss.cinn.cn/media/image/20251225/01c07a18752cac2eb831da0eb0fbe9654b.jpg@WQI4_ADnagYsfTfjER0j58t2Kl6kp4nTDzlEsDqUCE4@rs:fill:720:0@g:sm@q:75@.webp'
  },
  {
    title: '数智技术赋能工业现场，设备检修迈向知识化与协同化',
    summary: '面向复杂工业现场，知识检索、智能体协同和标准作业闭环成为设备运维升级方向。',
    source: '中国工业新闻网',
    date: '延伸阅读',
    link: 'https://www.cinn.cn/xyx/2026/07-15/K18x4jQ1.html',
    image: 'https://oss.cinn.cn/media/image/20260721/01e2130559a6fe9efc150badc2a5ecd27c.png@6HYqfKmZ6iyhK2etY2U08dCk0qTEjZe7KJBgdQhVQmE@rs:fill:720:0@g:sm@q:75@.webp'
  }
]
const defaultProfile = {
  ...mockUser,
  employeeId: 'YX-0824',
  skillLevel: '高级',
  phone: '138-0000-1024',
  specialties: ['发动机', '电气系统', '高风险作业确认'],
  bio: '专注动力设备检修、故障分析与标准作业执行。'
}
const defaultAccount = { account: 'yixiu', password: 'Yixiu2026!', name: '聪明的一修', profile: defaultProfile }
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
  if (name.includes('检索') || name.includes('故障')) return 'guanwei'
  if (name.includes('作业') || name.includes('工单') || name.includes('流程')) return 'zhiju'
  if (name.includes('知识') || name.includes('资料') || name.includes('图谱')) return 'bowen'
  if (name.includes('协作') || name.includes('联络') || name.includes('联系人')) return 'heming'
  if (name.includes('核查') || name.includes('复检') || name.includes('验收')) return 'mingjian'
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
const handleAvatarError = (event) => {
  event.target.src = '/static/agents/tiangong.png'
}
const avatarPalette = ['#dcefed', '#e9e2f7', '#f8e7d2', '#dce9f6', '#e3efdb']
const avatarFallback = (name = '一修') => {
  const label = String(name || '一修').replace(/[^\u4e00-\u9fa5A-Za-z0-9]/g, '').slice(-2) || '一修'
  const color = avatarPalette[[...label].reduce((sum, char) => sum + char.charCodeAt(0), 0) % avatarPalette.length]
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96"><rect width="96" height="96" rx="48" fill="${color}"/><circle cx="48" cy="40" r="18" fill="#fff" opacity=".92"/><path d="M18 88c3-21 15-31 30-31s27 10 30 31" fill="#fff" opacity=".92"/><text x="48" y="46" text-anchor="middle" font-family="Arial,sans-serif" font-size="16" font-weight="700" fill="#145f5a">${label}</text></svg>`
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`
}
const avatarFor = (avatar, name) => avatar && !String(avatar).includes('undefined') ? avatar : avatarFallback(name)
const handleContactAvatarError = (event, name) => { event.target.src = avatarFallback(name) }
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

const searchForm = reactive({ deviceName: '摩托车发动机总成', deviceModel: 'CG-125', faultCode: 'NOISE-02', category: '发动机', faultType: '异响', maintenanceLevel: '二级检修', query: '启动后气门区域有明显异响，热车后略有减轻，怠速不稳。' })
const searchFiles = ref([])
const searchAssistantFileInput = ref(null)
const assistantFiles = ref([])
const searchResult = ref(null)
const searchPanel = ref('multimodal')
const searchMultimodalExpanded = ref(true)
const searchTabs = [{ key: 'multimodal', label: '多模态检索' }, { key: 'history', label: '历史检索' }, { key: 'update', label: '沉淀更新' }]
const searchCapabilityCards = [
  { title: '图文证据融合', desc: '图片、文档、故障码统一建模', icon: 'search', tone: 'teal', metric: '多模态' },
  { title: '维修依据追溯', desc: '结果关联手册、SOP和历史案例', icon: 'file', tone: 'amber', metric: '可引用' },
  { title: '作业方案生成', desc: '自动整理工具、备件和安全项', icon: 'tool', tone: 'green', metric: '可转单' }
]
const searchProcessCards = [
  { title: '查看历史检索', desc: '复用相似故障的检索上下文', icon: 'clock', tone: 'blue', action: () => { searchPanel.value = 'history' } },
  { title: '沉淀知识条目', desc: '把有效结论提交到知识库审核', icon: 'check', tone: 'amber', action: () => { searchPanel.value = 'update'; prepareKnowledgeFromSearch() } },
  { title: '创建检修任务', desc: '将当前建议转为可执行工单', icon: 'tool', tone: 'teal', action: () => { if (searchResult.value) createTaskFromSearch(recommendationResult.value); else toast('请先完成一次智能检索') } },
  { title: '打开知识图谱', desc: '查看设备、故障和资料关系', icon: 'network', tone: 'green', action: () => { activePage.value = 'knowledge'; knowledgePanel.value = 'network' } }
]
const searchTemplatePrompts = [
  { title: '分析原因', icon: 'search', prompt: '请根据当前设备、故障现象和上传资料，分析最可能的故障原因，并按优先级排序。' },
  { title: '生成步骤', icon: 'file', prompt: '请把检索结果整理成现场可执行的检修步骤，包含安全确认、检测位置和复检标准。' },
  { title: '提取风险', icon: 'shield', prompt: '请识别当前检修任务中的安全风险、停机建议和必须二次确认的步骤。' },
  { title: '转为任务', icon: 'check', prompt: '请根据当前检索结论生成一条检修任务草稿，包含负责人、工具、备件和计划完成时间。' }
]
const searchHistory = ref([
  { id: 'history-1', title: 'CG-125 发动机气门异响排查', deviceName: '摩托车发动机总成', model: 'CG-125', faultCode: 'NOISE-02', category: '发动机', faultType: '异响', maintenanceLevel: '二级检修', query: '启动后气门区域异响，热车后减轻，怠速不稳。', confidence: 91, time: '今日 09:42' },
  { id: 'history-2', title: 'ZK-320 配电柜过热检索', deviceName: '配电柜', model: 'ZK-320', faultCode: 'TEMP-04', category: '电气系统', faultType: '过热', maintenanceLevel: '二级检修', query: '柜内温度偏高，接触器区域热像异常，散热风道疑似堵塞。', confidence: 88, time: '昨日 16:18' },
  { id: 'history-3', title: '液压站油路渗漏定位', deviceName: '液压站', model: 'HYD-220', faultCode: 'LEAK-01', category: '液压系统', faultType: '渗漏', maintenanceLevel: '一级巡检', query: '回油管接头处有油迹，压力波动，停机后仍有少量滴漏。', confidence: 84, time: '本周一 11:05' }
])
const historyInsightCards = [
  { title: '高频设备', desc: '发动机与配电柜检索占比最高', value: '2 类' },
  { title: '常见线索', desc: '异响、过热、渗漏集中出现', value: '3 类' },
  { title: '可复用资料', desc: '手册、SOP、历史案例可直接带入', value: '9 份' },
  { title: '建议动作', desc: '优先沉淀高置信度检索结论', value: '2 条' }
]
const historyTraceCards = [
  { title: '同型号追溯', desc: 'CG-125 异响记录已关联历史案例、维修手册与复检报告', meta: '6 条链路', icon: 'network', tone: 'teal' },
  { title: '高风险复用', desc: '配电柜过热检索包含停电验电、热像复测和二次确认', meta: '3 项提醒', icon: 'shield', tone: 'red' },
  { title: '资料缺口', desc: '液压站渗漏记录缺少现场照片，建议补充接头局部图', meta: '1 项待补', icon: 'file', tone: 'amber' }
]
const knowledgeUpdateSteps = [
  { title: '提取结论', desc: '整理故障现象、原因与检测位置' },
  { title: '核对依据', desc: '绑定手册、SOP、案例和现场图片' },
  { title: '人工修正', desc: '补全标签、设备型号与适用范围' },
  { title: '审核入库', desc: '通过后进入知识图谱与智能召回' }
]
const updateProgressCards = computed(() => [
  { title: '引用依据', value: `${searchResult.value?.references?.length || 0} 份`, desc: '手册、SOP、案例', icon: 'file', tone: 'blue' },
  { title: '人工标签', value: `${knowledgeForm.tagText ? knowledgeForm.tagText.split(/[，,]/).filter(Boolean).length : 0} 个`, desc: '用于检索召回', icon: 'network', tone: 'teal' },
  { title: '待审核', value: `${pendingKnowledge.value.length} 条`, desc: '等待管理员确认', icon: 'clock', tone: 'amber' },
  { title: '图谱同步', value: searchResult.value ? '可生成' : '待研判', desc: '关系节点增量更新', icon: 'check', tone: 'green' }
])
const updateQualityRules = [
  { title: '来源可追溯', desc: '绑定手册、工单、现场记录或专家意见' },
  { title: '结论可复检', desc: '故障原因、检测方法和验收标准可现场验证' },
  { title: '关系可入图', desc: '至少包含设备、故障、原因、方案中的两个实体' }
]
const resultTab = ref('全部')
const resultTabs = ['全部', '维修手册', '历史故障案例', '标准作业流程 SOP', '安全操作规范', '推荐检修方案']
const resultTabCopy = {
  '全部': '汇总展示与当前故障最相关的知识资料和检修建议',
  '维修手册': '查看设备结构、参数标准和厂家检修说明',
  '历史故障案例': '参考相似现象、原因判断和现场处置记录',
  '标准作业流程 SOP': '按标准步骤执行检查、拆装、复测和验收',
  '安全操作规范': '核对作业许可、风险隔离和安全确认要求',
  '推荐检修方案': '根据当前多模态分析结果生成建议作业路径'
}

const taskPanel = ref('overview')
const taskTabs = [{ key: 'overview', label: '今日概览' }, { key: 'manage', label: '任务管理' }, { key: 'recheck', label: '复检评估' }, { key: 'contacts', label: '联系人' }]
const taskFilters = reactive({ status: 'all', severity: 'all', category: 'all', faultType: 'all', assignee: 'all', overdue: 'all', keyword: '' })
const taskView = ref('table')
const showTaskForm = ref(false)
const taskForm = reactive({ equipment_name: '', equipment_no: '', equipment_model: '', severity: 'medium', assignee_name: user.name, due_at: '', description: '' })
const recheckForms = reactive({})
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

const knowledgePanel = ref('network')
const knowledgeTabs = [{ key: 'network', label: '知识网络' }, { key: 'files', label: '文件管理' }, { key: 'library', label: '技术资料库' }]
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
const fileKeyword = ref('')
const fileType = ref('all')
const fileView = ref('card')
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
    quickTitle: '打开任务管理',
    quickDesc: '查看工单、筛选风险、执行状态流转',
    placeholder: '输入任务操作或复检意见',
    actions: ['新建任务', '流转任务', '进入复检', '联系人']
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
    quickTitle: '执行复检核查',
    quickDesc: '核对复测数据、安全结果和最终验收意见',
    placeholder: '输入复检意见或验收问题',
    actions: ['保存复检', '退回返工', '查看标准', '生成验收意见']
  },
  knowledge: {
    ...agentProfileMap.bowen,
    icon: 'network',
    status: 'busy',
    statusText: '处理中',
    welcome: '我是博闻，负责整理技术资料、维护知识网络，并把有效检修经验沉淀成系统知识。',
    sampleAsk: '这份维修资料能不能加入知识库？',
    sampleAnswer: '需要先通过文件审核和解析，确认设备、型号、故障、SOP 与原始文件一致。',
    quickTitle: '进入文件管理',
    quickDesc: '上传资料、预览文件、查看解析与审核状态',
    placeholder: '询问资料、文件解析或知识沉淀',
    actions: ['文件管理', '知识网络', '提交沉淀', '资料检索']
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
const operatorProfile = computed(() => {
  const contextual = operatorProfiles[operatorKey.value] || operatorProfiles.home
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
const currentOperatorMessages = computed(() => operatorMessages.value.filter((message) => message.global || message.page === activePage.value))
const todayCompletion = computed(() => {
  const total = overview.stats.pending + overview.stats.inProgress + overview.stats.review + overview.stats.completed
  return Math.round(overview.stats.completed / Math.max(total, 1) * 100)
})

const statCards = computed(() => [
  { key: 'today', label: '今日新增任务', value: overview.stats.todayNew, hint: '点击进入任务管理', page: 'tasks', panel: 'manage' },
  { key: 'pending', label: '待处理任务', value: overview.stats.pending, hint: '自动筛选待处理', page: 'tasks', panel: 'manage', status: 'pending' },
  { key: 'progress', label: '进行中任务', value: overview.stats.inProgress, hint: '查看检修中工单', page: 'tasks', panel: 'manage', status: 'in_progress' },
  { key: 'risk', label: '高风险任务', value: overview.stats.highRisk, hint: '优先处理', page: 'tasks', panel: 'manage', severity: 'high' },
  { key: 'review', label: '待复检任务', value: overview.stats.review, hint: '进入复检评估', page: 'tasks', panel: 'recheck' },
  { key: 'done', label: '已完成任务', value: overview.stats.completed, hint: '查看归档', page: 'tasks', panel: 'manage', status: 'completed' },
  { key: 'kb', label: '知识库资料总量', value: overview.stats.knowledgeTotal, hint: '进入技术资料库', page: 'knowledge', panel: 'library' },
  { key: 'week', label: '本周新增知识', value: overview.stats.weekKnowledge, hint: '进入沉淀更新', page: 'search', panel: 'update' },
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
      tag: task.status === 'review' ? '复检安排' : task.severity === 'high' ? '高风险' : '工作安排',
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
      title: '动力设备检修班组碰头会',
      desc: '同步高风险工单、复检排期和备件到位情况',
      people: `参与人员：${contacts.value.slice(0, 3).map((item) => item.name).join('、') || '聪明的一修、王铭、赵宁'}`,
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
    title: '暂无固定检修安排',
    desc: '可用于临时支援、资料整理或知识沉淀',
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
  if (item.important || item.tag === '高风险' || item.task?.severity === 'high') return 'critical'
  if (item.tag?.includes('复检') || item.task?.status === 'review') return 'review'
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
  review: '复检',
  meeting: '协作',
  knowledge: '资料',
  done: '已完成',
  quiet: '空闲',
  work: item.tag || '工作'
}[scheduleTone(item)] || item.tag || '工作')
const alerts = computed(() => [
  { title: '高风险工单', desc: `${tasks.value.filter((task) => task.severity === 'high').length} 个任务需要二次确认`, tone: 'danger', icon: 'bell', action: () => goStat({ page: 'tasks', panel: 'manage', severity: 'high' }) },
  { title: '待复检任务', desc: `${tasks.value.filter((task) => task.status === 'review').length} 个任务等待复测数据`, tone: 'amber', icon: 'check', action: () => goStat({ page: 'tasks', panel: 'recheck' }) },
  { title: '知识审核异常', desc: '1 份资料解析部分成功，请人工复核', tone: 'violet', icon: 'network', action: () => goStat({ page: 'knowledge', panel: 'files' }) },
  { title: '智能服务状态', desc: systemStatus.ai, tone: 'teal', icon: 'cpu', action: () => activePage.value = 'profile' }
])
const quickActions = [
  { label: '发起智能检索', desc: '检索故障与资料', icon: 'search', tone: 'blue', action: () => activePage.value = 'search' },
  { label: '新建检修任务', desc: '创建现场工单', icon: 'wrench', tone: 'teal', action: () => { activePage.value = 'tasks'; taskPanel.value = 'manage'; showTaskForm.value = true } },
  { label: '上传维修资料', desc: '补充知识文件', icon: 'network', tone: 'violet', action: () => { activePage.value = 'knowledge'; knowledgePanel.value = 'files' } },
  { label: '查看高风险任务', desc: '优先确认风险', icon: 'bell', tone: 'amber', action: () => goStat({ page: 'tasks', panel: 'manage', severity: 'high' }) },
  { label: '进入复检评估', desc: '核对复测结果', icon: 'check', tone: 'blue', action: () => goStat({ page: 'tasks', panel: 'recheck' }) },
  { label: '查看知识网络', desc: '浏览知识关系', icon: 'network', tone: 'teal', action: () => goStat({ page: 'knowledge', panel: 'network' }) },
  { label: '联系现场负责人', desc: '发起协作沟通', icon: 'user', tone: 'violet', action: () => goStat({ page: 'tasks', panel: 'contacts' }) },
  { label: '个人检修记录', desc: '查看工作档案', icon: 'dashboard', tone: 'amber', action: () => activePage.value = 'profile' }
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
  goStat({ page: 'knowledge', panel: 'library' })
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
    { label: '待接收', value: tasks.value.filter((task) => task.status === 'pending').length, hint: '等待派工确认', filter: { status: 'pending' } },
    { label: '检修中', value: tasks.value.filter((task) => task.status === 'in_progress').length, hint: '现场处理中', filter: { status: 'in_progress' } },
    { label: '待复检', value: tasks.value.filter((task) => task.status === 'review').length, hint: '等待验收复核', filter: { status: 'review' } },
    { label: '高风险', value: tasks.value.filter((task) => task.severity === 'high').length, hint: '优先安全确认', filter: { severity: 'high' } },
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
    { key: 'engine', title: '发动机检修流程', desc: '异响、点火与温升任务优先推送测量和复测步骤', count: source.filter((task) => task.equipment_category === '发动机' || task.equipment_name?.includes('发动机')).length, filter: { category: '发动机' } },
    { key: 'electric', title: '电气安全作业', desc: '电气设备强制校验停电、验电、挂牌和复测记录', count: source.filter((task) => task.equipment_category === '电气系统' || task.equipment_name?.includes('配电')).length, filter: { category: '电气系统' } },
    { key: 'highRisk', title: '高风险合规校验', desc: '高风险作业需二次确认和完整证据链', count: highRisk, filter: { severity: 'high' } },
    { key: 'process', title: '执行中步骤闭环', desc: '跟踪未完成 SOP 步骤，防止跳步进入复检', count: inProgress, filter: { status: 'in_progress' } }
  ]
})
const taskOpsCards = computed(() => {
  const pending = tasks.value.filter((task) => task.status === 'pending')
  const highRisk = tasks.value.filter((task) => task.severity === 'high')
  const review = tasks.value.filter((task) => task.status === 'review')
  const overdue = tasks.value.filter(isTaskOverdue)
  return [
    { label: '现场接收', title: `${pending.length} 项待接收`, desc: pending[0]?.equipment_name ? `优先确认 ${pending[0].equipment_name} 工单` : '暂无待接收工单', icon: 'check', tone: 'amber', action: () => filterTaskBy('status', 'pending') },
    { label: '安全风险', title: `${highRisk.length} 项高风险`, desc: highRisk[0]?.current_step ? `当前步骤：${highRisk[0].current_step}` : '高风险任务已清空', icon: 'shield', tone: 'red', action: () => filterTaskBy('severity', 'high') },
    { label: '复检闭环', title: `${review.length} 项待复检`, desc: review[0]?.assignee_name ? `责任人：${review[0].assignee_name}` : '暂无待复检任务', icon: 'file', tone: 'teal', action: () => { taskPanel.value = 'recheck' } },
    { label: '排期预警', title: `${overdue.length} 项逾期`, desc: overdue[0]?.workOrderNo ? `${overdue[0].workOrderNo} 需要协调` : '排期正常', icon: 'clock', tone: 'blue', action: () => { taskFilters.overdue = 'yes'; taskPanel.value = 'manage' } }
  ]
})
const recheckDashboard = computed(() => {
  const total = Math.max(recheckTasks.value.length, 1)
  const passed = recheckTasks.value.filter((task) => recheckForms[task.id]?.result === '通过').length
  const rework = recheckTasks.value.filter((task) => ['返工', '不通过'].includes(recheckForms[task.id]?.result)).length
  const filled = recheckTasks.value.filter((task) => recheckForms[task.id]?.comment?.trim()).length
  return [
    { label: '一次通过预估', value: `${Math.round(passed / total * 100)}%`, hint: `${passed}/${recheckTasks.value.length} 项`, icon: 'check', tone: 'green' },
    { label: '返工风险', value: rework, hint: '需明确整改要求', icon: 'shield', tone: rework ? 'red' : 'teal' },
    { label: '记录完整度', value: `${Math.round(filled / total * 100)}%`, hint: '复测数据与意见', icon: 'file', tone: 'blue' },
    { label: '待验收设备', value: recheckTasks.value.length, hint: '按风险排序核查', icon: 'tool', tone: 'amber' }
  ]
})
const recheckChecklist = (task = {}) => {
  const form = recheckForms[task.id] || {}
  return [
    { label: '运行状态', desc: task.progress >= 90 ? '已完成作业' : '仍需补充步骤', ok: task.progress >= 90 },
    { label: '复测数据', desc: form.comment?.trim() ? '已填写记录' : '等待复测记录', ok: Boolean(form.comment?.trim()) },
    { label: '安全确认', desc: task.severity === 'high' ? '高风险需二次确认' : '常规安全项', ok: task.severity !== 'high' || Boolean(form.comment?.trim()) },
    { label: '资料归档', desc: task.references?.length ? '已关联依据' : '建议补充依据', ok: Boolean(task.references?.length) }
  ]
}
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
  { id: `${task.id}-create`, time: task.created_at, text: `${task.title} 已创建，负责人 ${task.assignee_name}` },
  { id: `${task.id}-step`, time: task.due_at, text: `${task.equipment_name} 当前步骤：${task.current_step}，进度 ${task.progress}%` },
  ...(task.status === 'review' ? [{ id: `${task.id}-review`, time: task.due_at, text: `${task.title} 已提交复检，等待复测数据` }] : []),
  ...(index === 0 ? [{ id: `${task.id}-risk`, time: task.created_at, text: `${task.title} 已标记为重点任务，需确认安全措施` }] : [])
]).slice(0, 10))
const taskBoardColumns = computed(() => ['pending', 'in_progress', 'review', 'completed'].map((key) => ({ key, label: statusText(key), tasks: filteredTasks.value.filter((task) => task.status === key) })))
const myTasks = computed(() => tasks.value.filter((item) => item.assignee_name === user.name || item.collaborators?.includes(user.name)))
const profileSections = computed(() => {
  const assigned = tasks.value.filter((task) => task.assignee_name === user.name)
  const pending = assigned.filter((task) => task.status === 'pending')
  const processing = myTasks.value.filter((task) => task.status === 'in_progress')
  const review = myTasks.value.filter((task) => task.status === 'review')
  const completed = myTasks.value.filter((task) => task.status === 'completed')
  const highRisk = myTasks.value.filter((task) => task.severity === 'high')
  const overdue = myTasks.value.filter((task) => isTaskOverdue(task))
  const approvedKnowledge = knowledge.value.filter((item) => item.status === 'approved')
  const pendingKnowledgeItems = knowledge.value.filter((item) => item.status !== 'approved')
  const recentFiles = files.value.slice(0, 2).map((file) => ({ title: file.name, desc: file.category || file.type, icon: 'file', page: 'knowledge', panel: 'files', meta: file.parseStatus }))
  const recentTasks = myTasks.value.slice(0, 2).map((task) => ({ title: task.title, desc: statusText(task.status), icon: 'clock', page: 'tasks', panel: 'manage', meta: `${task.progress}%` }))

  return [
    {
      key: 'today',
      icon: 'calendar',
      group: '今日任务概览',
      title: '今日待办',
      span: 'span-8',
      action: '进入检修任务',
      page: 'tasks',
      panel: 'manage',
      metrics: [
        { label: '待接收', value: pending.length },
        { label: '检修中', value: processing.length },
        { label: '待复检', value: review.length },
        { label: '高风险', value: highRisk.length }
      ],
      items: myTasks.value.slice(0, 4).map((task) => ({ title: task.title, desc: task.current_step || statusText(task.status), icon: 'wrench', page: 'tasks', panel: 'manage', meta: `${task.progress}%` }))
    },
    {
      key: 'ability',
      icon: 'chart',
      group: '检修能力画像',
      title: '能力画像',
      span: 'span-4',
      metrics: [
        { label: '完成率', value: '94%' },
        { label: '平均处理', value: '3.4h' },
        { label: '擅长方向', value: user.specialties?.length || 0 }
      ],
      items: [
        { title: user.specialties?.join(' / ') || '设备检修', desc: '擅长方向', icon: 'tool' },
        { title: '高压安全作业', desc: '培训已完成', icon: 'shield' },
        { title: '发动机异响排查', desc: '高频能力', icon: 'search' }
      ]
    },
    {
      key: 'records',
      icon: 'file',
      group: '我的任务与记录',
      title: '任务记录',
      span: 'span-4',
      action: '查看任务列表',
      page: 'tasks',
      panel: 'manage',
      metrics: [
        { label: '由我负责', value: assigned.length },
        { label: '我参与', value: myTasks.value.length },
        { label: '已完成', value: completed.length }
      ],
      items: myTasks.value.slice(0, 3).map((task) => ({ title: task.title, desc: statusText(task.status), icon: 'wrench', page: 'tasks', panel: 'manage', meta: task.due_at || '查看' }))
    },
    {
      key: 'contribution',
      icon: 'network',
      group: '我的知识贡献',
      title: '知识贡献',
      span: 'span-4',
      action: '进入沉淀更新',
      page: 'search',
      panel: 'update',
      metrics: [
        { label: '已通过', value: approvedKnowledge.length },
        { label: '审核中', value: pendingKnowledgeItems.length },
        { label: '资料引用', value: approvedKnowledge.reduce((sum, item) => sum + (item.citations || 0), 0) }
      ],
      items: knowledge.value.slice(0, 3).map((item) => ({ title: item.title, desc: item.status === 'approved' ? '已通过' : '待完善', icon: 'file', page: 'search', panel: 'update', meta: `${item.citations || 0} 引用` }))
    },
    {
      key: 'quality',
      icon: 'shield',
      group: '核查与质量评分',
      title: '质量评分',
      span: 'span-4',
      action: '进入复检评估',
      page: 'tasks',
      panel: 'recheck',
      metrics: [
        { label: '复检通过率', value: '92%' },
        { label: '逾期任务', value: overdue.length },
        { label: '风险待确认', value: highRisk.length }
      ],
      items: [
        { title: '配电柜过热复核', desc: '温升数据', icon: 'shield', page: 'tasks', panel: 'recheck', meta: '待核查' },
        { title: '液压站渗漏跟踪', desc: '压力稳定', icon: 'check', page: 'tasks', panel: 'recheck', meta: '通过' },
        { title: '核查建议', desc: '补充照片', icon: 'bot', page: 'tasks', panel: 'recheck', meta: '建议' }
      ]
    },
    {
      key: 'recent',
      icon: 'clock',
      group: '最近浏览',
      title: '最近浏览',
      span: 'span-4',
      items: [...recentTasks, ...recentFiles].slice(0, 4)
    },
    {
      key: 'tools',
      icon: 'zap',
      group: '常用工具入口',
      title: '常用工具',
      span: 'span-4',
      items: [
        { title: '智能检索', desc: '找资料', icon: 'search', page: 'search', panel: 'multimodal' },
        { title: '新建任务', desc: '开工单', icon: 'wrench', page: 'tasks', panel: 'manage' },
        { title: '上传资料', desc: '入库', icon: 'file', page: 'knowledge', panel: 'files' },
        { title: '联系专家', desc: '协作', icon: 'user', page: 'tasks', panel: 'contacts' }
      ]
    },
    {
      key: 'settings',
      icon: 'settings',
      group: '账号与系统设置',
      title: '账号设置',
      span: 'span-4',
      items: [
        { title: '身份卡', desc: currentAccount.value || '未登录', icon: 'user', action: 'edit-profile' },
        { title: '风险提醒', desc: '开启', icon: 'bell' },
        { title: '复检提醒', desc: '开启', icon: 'check' },
        { title: '退出账号', desc: '安全退出', icon: 'settings', action: 'logout' }
      ]
    }
  ]
})
const profileQuickCards = computed(() => {
  const assigned = tasks.value.filter((task) => task.assignee_name === user.name || task.assignee === user.name)
  const review = myTasks.value.filter((task) => task.status === 'review')
  const completed = myTasks.value.filter((task) => task.status === 'completed')
  const highRisk = myTasks.value.filter((task) => task.severity === 'high')
  const approvedKnowledge = knowledge.value.filter((item) => item.status === 'approved')
  return [
    { title: '待处理事项', value: assigned.filter((task) => task.status !== 'completed').length, desc: '待办任务', icon: 'calendar', tone: 'blue', page: 'tasks', panel: 'manage' },
    { title: '我的任务', value: myTasks.value.length, desc: '全部工单', icon: 'wrench', tone: 'violet', page: 'tasks', panel: 'manage' },
    { title: '检修档案', value: completed.length, desc: '完成记录', icon: 'file', tone: 'red', page: 'profile' },
    { title: '知识贡献', value: approvedKnowledge.length, desc: '已入库', icon: 'network', tone: 'orange', page: 'search', panel: 'update' },
    { title: '质量评分', value: '96', desc: '核查评分', icon: 'shield', tone: 'gold', page: 'tasks', panel: 'recheck' },
    { title: '最近浏览', value: Math.max(8, review.length + highRisk.length + files.value.length), desc: '查看记录', icon: 'clock', tone: 'cyan', page: 'knowledge', panel: 'files' }
  ]
})
const profileSecurityItems = computed(() => [
  { title: '手机号绑定', desc: '138****5678', meta: '已绑定', icon: 'user', action: 'edit-profile' },
  { title: '登录密码', desc: '建议定期更新', meta: '正常', icon: 'shield' },
  { title: '登录设备管理', desc: '已登录 3 台设备', meta: '查看', icon: 'cpu' },
  { title: '二次验证', desc: '高风险操作确认', meta: '已开启', icon: 'check' },
  { title: '退出账号', desc: currentAccount.value || '当前账号', meta: '退出', icon: 'settings', action: 'logout' }
])
const profileToolItems = computed(() => [
  { title: '修改资料', desc: '编辑个人档案', icon: 'user', action: 'edit-profile' },
  { title: '任务管理', desc: '查看我的工单', icon: 'wrench', page: 'tasks', panel: 'manage' },
  { title: '资料上传', desc: '维护技术资料', icon: 'file', page: 'knowledge', panel: 'files' },
  { title: '智能检索', desc: '检索维修知识', icon: 'search', page: 'search', panel: 'multimodal' },
  { title: '复检评估', desc: '质量核查', icon: 'shield', page: 'tasks', panel: 'recheck' },
  { title: '通知偏好', desc: '消息提醒设置', icon: 'bell' }
])
const profileRecentItems = computed(() => {
  const taskItems = myTasks.value.slice(0, 3).map((task) => ({
    title: task.title,
    desc: `${statusText(task.status)} · ${task.current_step || '等待处理'}`,
    icon: 'wrench',
    page: 'tasks',
    panel: 'manage',
    meta: task.updated_at || task.due_at || '今日'
  }))
  const fileItems = files.value.slice(0, 2).map((file) => ({
    title: file.name,
    desc: file.category || file.type || '技术资料',
    icon: 'file',
    page: 'knowledge',
    panel: 'files',
    meta: file.updated_at || file.parseStatus || '最近'
  }))
  return [...taskItems, ...fileItems].slice(0, 5)
})
const profileGrowthScore = computed(() => 8200 + myTasks.value.length * 70 + knowledge.value.filter((item) => item.status === 'approved').length * 25)
const profileGrowthBenefits = [
  { title: '专家协作', icon: 'user' },
  { title: '知识沉淀', icon: 'network' },
  { title: '复检评分', icon: 'shield' },
  { title: '报告归档', icon: 'file' }
]
const profilePreferenceItems = computed(() => [
  { title: '主题模式', icon: 'settings', meta: '浅色纸质' },
  { title: '消息提醒', icon: 'bell', meta: '已开启' },
  { title: '默认任务视图', icon: 'calendar', meta: '工作台' },
  { title: '风险提醒', icon: 'shield', meta: '高优先级' }
])
const profileWorkSection = computed(() => profileSections.value.find((section) => section.key === 'work'))
const profileScheduleSection = computed(() => profileSections.value.find((section) => section.key === 'schedule'))
const profileFilesSection = computed(() => profileSections.value.find((section) => section.key === 'files'))
const profileSettingsSection = computed(() => profileSections.value.find((section) => section.key === 'settings'))
const profileContributionSection = computed(() => profileSections.value.find((section) => section.key === 'contribution'))
const recheckTasks = computed(() => tasks.value.filter((task) => ['review', 'completed'].includes(task.status) || task.progress >= 80))
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
  avatar: '/static/agents/heming.png',
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
  { id: 'task-room-1', kind: 'group', name: 'ZK-320 过热检修群', avatar: '/static/agents/heming.png', position: '任务群组', department: '动力设备检修一组', specialty: '高风险任务协作', devices: ['配电柜', 'ZK-320'], currentTask: 'ZK-320 配电柜过热检修', workload: 78, lastMessage: '已上传红外测温图片', unread: conversationUnread('task-room-1', 3), taskNo: 'YX-20260803-001', risk: 'high' },
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
const filteredFiles = computed(() => files.value.filter((file) => {
  const keywordOk = !fileKeyword.value || JSON.stringify(file).includes(fileKeyword.value)
  const typeOk = fileType.value === 'all' || file.type === fileType.value
  const folderOk = activeFolder.value === '全部文件' || file.folder === activeFolder.value || file.category === activeFolder.value
  return keywordOk && typeOk && folderOk
}))
const extraFileSamples = [
  { id: 'sample-file-gearbox', name: '减速机轴承温升排查记录.docx', type: 'Word', size: '1.8 MB', category: '检修报告', folder: '检修报告', equipment: '减速机', model: 'RX-450', uploader: '唐忆哲', uploaded_at: '2026-08-02 09:26', auditStatus: '已审核', parseStatus: '解析完成', version: 'v1.2' },
  { id: 'sample-file-air-compressor', name: '空压机保养周期与点检表.xlsx', type: 'Excel', size: '860 KB', category: '标准作业流程', folder: '标准作业流程', equipment: '空压机', model: 'GA-75', uploader: '陈程', uploaded_at: '2026-08-01 15:44', auditStatus: '已审核', parseStatus: '解析完成', version: 'v1.0' },
  { id: 'sample-file-hydraulic', name: '液压系统油路清洗规范.pdf', type: 'PDF', size: '3.4 MB', category: '液压系统', folder: '液压系统', equipment: '液压站', model: 'HYD-220', uploader: '聪明的一修', uploaded_at: '2026-07-30 11:12', auditStatus: '已审核', parseStatus: '解析完成', version: 'v2.0' },
  { id: 'sample-file-motor', name: '三相电机绝缘测试报告.pdf', type: 'PDF', size: '2.1 MB', category: '电气系统', folder: '电气系统', equipment: '三相异步电机', model: 'Y2-160M', uploader: '李志勇', uploaded_at: '2026-07-29 14:08', auditStatus: '已审核', parseStatus: '解析完成', version: 'v1.1' },
  { id: 'sample-file-install', name: '现场安装验收照片-配电柜.png', type: '图片', size: '4.7 MB', category: '现场图片', folder: '现场图片', equipment: '配电柜', model: 'ZK-320', uploader: '唐忆罗', uploaded_at: '2026-07-27 17:36', auditStatus: '待审核', parseStatus: '图片识别完成', version: 'v1.0' },
  { id: 'sample-file-engine', name: '发动机气门间隙调整 SOP.docx', type: 'Word', size: '1.2 MB', category: '发动机资料', folder: '发动机资料', equipment: '发动机总成', model: 'CG-125', uploader: '博闻', uploaded_at: '2026-07-26 10:51', auditStatus: '已审核', parseStatus: '解析完成', version: 'v1.4' },
  { id: 'sample-file-recheck', name: '复检数据归档模板.xlsx', type: 'Excel', size: '540 KB', category: '复检报告', folder: '复检报告', equipment: '通用设备', model: '通用', uploader: '明鉴', uploaded_at: '2026-07-24 16:20', auditStatus: '已审核', parseStatus: '解析完成', version: 'v1.0' },
  { id: 'goview-file-manual', name: '汽修宝典-汽车维修手册资料索引.pdf', type: 'PDF', size: '2.6 MB', category: '维修手册', folder: '汽车维修资料', equipment: '汽车发动机系统', model: '通用乘用车', uploader: '博闻', uploaded_at: '2026-08-15 10:12', auditStatus: '已审核', parseStatus: '解析完成', version: 'v1.0', source: 'https://www.goviewtech.com/index.html' },
  { id: 'goview-file-circuit', name: '汽修宝典-汽车电路图检索说明.pdf', type: 'PDF', size: '1.9 MB', category: '电气原理图', folder: '汽车维修资料', equipment: '汽车电气系统', model: '通用乘用车', uploader: '博闻', uploaded_at: '2026-08-15 10:16', auditStatus: '已审核', parseStatus: '解析完成', version: 'v1.0', source: 'https://www.goviewtech.com/index.html' },
  { id: 'goview-file-dtc', name: '汽修宝典-热门故障码问答整理.docx', type: 'Word', size: '980 KB', category: '故障案例', folder: '汽车维修资料', equipment: 'OBD诊断系统', model: '通用', uploader: '观微', uploaded_at: '2026-08-15 10:20', auditStatus: '已审核', parseStatus: '解析完成', version: 'v1.0', source: 'https://www.goviewtech.com/index.html' },
  { id: 'goview-file-video', name: '汽修宝典-维修视频学习清单.xlsx', type: 'Excel', size: '620 KB', category: '检修视频', folder: '汽车维修资料', equipment: '汽车底盘与发动机', model: '通用', uploader: '博闻', uploaded_at: '2026-08-15 10:24', auditStatus: '已审核', parseStatus: '解析完成', version: 'v1.0', source: 'https://www.goviewtech.com/index.html' }
]
const extraKnowledgeSamples = [
  { id: 'goview-kb-manual', title: '汽修宝典官网：汽车维修手册资料库概括', type: '维修手册', category: '汽车维修资料', equipment: '汽车发动机系统', model: '通用乘用车', summary: '汽修宝典官网定位为汽修资料与维修技术入口，可用于归纳汽车维修手册、车型资料、部件拆装与检测信息。', content: '来源页面公开说明其面向汽修技师提供维修资料、找资料、问问题和学知识能力。本条目仅作检修知识索引，用于一修知识检索和图谱关联。', tags: ['汽车维修', '维修手册', '资料库', '找资料'], source: 'https://www.goviewtech.com/index.html', status: 'approved', citations: 18, updated_at: '2026-08-15 10:12' },
  { id: 'goview-kb-circuit', title: '汽车电路图与电气诊断资料索引', type: '技术资料', category: '电气原理图', equipment: '汽车电气系统', model: '通用乘用车', summary: '围绕电路图、线束、传感器、执行器和供电接地关系建立诊断索引，适合与工业电气系统检测方法形成共享节点。', content: '汽修宝典官网栏目包含电路图相关入口。本条目抽象为汽车电气图纸检索节点，便于一修图谱关联电气检测、故障码和安全断电流程。', tags: ['汽车电气', '电路图', '检测方法', '线束'], source: 'https://www.goviewtech.com/index.html', status: 'approved', citations: 12, updated_at: '2026-08-15 10:16' },
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
const fileTreeItems = computed(() => {
  const rows = [
    { id: 'root-system', name: '系统知识库', level: 0, hasChildren: true, expanded: true, count: files.value.length },
    { id: 'root-doc', name: '文档', level: 1, hasChildren: false, expanded: false, count: fileCountForFolder('维修手册') },
    { id: 'root-client', name: '客户', level: 1, hasChildren: false, expanded: false, count: 0 },
    { id: 'root-project', name: '项目', level: 0, hasChildren: true, expanded: true, count: files.value.length }
  ]
  const pushFolder = (folder, level) => {
    const children = fileFolderChildren.value[folder] || []
    const expanded = isFileFolderExpanded(folder)
    rows.push({ id: `folder-${folder}`, name: folder, level, hasChildren: children.length > 0, expanded, count: fileCountForFolder(folder) })
    if (expanded) children.forEach((child) => pushFolder(child, level + 1))
  }
  ;(fileFolderChildren.value['项目'] || []).forEach((folder) => pushFolder(folder, 1))
  return rows
})

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
  initRecheckForms()
}

const initRecheckForms = () => {
  tasks.value.forEach((task) => {
    if (!recheckForms[task.id]) recheckForms[task.id] = { result: task.recheck?.result || '通过', comment: task.recheck?.comment || '' }
  })
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
    activePage.value = 'knowledge'
    knowledgePanel.value = 'library'
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
  operatorMessages.value.push({
    id: `agent-${Date.now()}`,
    page: activePage.value,
    role: 'assistant',
    text: `${agent.name}已接入当前页面。${agent.lastResult || agent.duty}`
  })
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
const updateGraphChart = () => {
  if (!graphChartInstance) return
  graphChartInstance.setOption(buildGraphChartOption(), true)
}
const handleGraphResize = () => {
  graphChartInstance?.resize()
}
const settleGraphChart = () => {
  nextTick(() => {
    tryInitGraphChart()
    requestAnimationFrame(() => {
      updateGraphChart()
      graphChartInstance?.resize()
      window.setTimeout(() => graphChartInstance?.resize(), 180)
      window.setTimeout(() => { updateGraphChart(); graphChartInstance?.resize() }, 360)
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
      content: '# 检修班组例会纪要\n## 时间\n2026年8月3日 14:00\n## 参会人员\n聪明的一修、李志勇、唐忆罗、陈程\n## 议题\n1. 本周检修任务进展\n2. 配电柜过热工单风险确认\n3. CG-125发动机异响排查方案\n## 行动计划\n- 聪明的一修负责配电柜停机检修\n- 李志勇跟进发动机拆检',
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
const runProfileAction = (section) => {
  if (!section) return
  if (section.page) goStat({ page: section.page, panel: section.panel })
  else toast('已打开个人设置')
}
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
  if (card.type === 'knowledge') return goStat({ page: 'knowledge', panel: 'network' })
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
  return ['该资料已纳入一修知识库，可编辑完善内容或作为智能检索依据。']
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
const severityText = (value) => ({ low: '低风险', medium: '中风险', high: '高风险', critical: '严重风险' }[value] || value || '中风险')
const statusText = (value) => ({ pending: '待处理', in_progress: '检修中', review: '待复检', completed: '已完成', paused: '已暂停', rejected: '已退回', overdue: '已逾期' }[value] || value || '待处理')
const knowledgeStatusText = (value) => ({ pending: '待人工审核', approved: '已审核入库', rejected: '已退回修改' }[value] || value || '待人工审核')
const modalityText = (value) => ({ text: '文本描述', equipment_model: '设备型号', image: '故障图片', document: '维修文档', file: '现场附件' }[value] || value)
const cleanKnowledgePart = (value) => String(value ?? '').replace(/^\s*[.。·]{1,}\s*$/, '').trim()
const knowledgeTypeText = (item) => cleanKnowledgePart(item.type || item.category) || '检修知识'
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
  return lines.length ? lines.slice(0, 4) : ['该资料已纳入一修知识库，可查看详情或作为智能检索依据。']
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
  operatorMessages.value = operatorMessages.value.filter((message) => message.page !== activePage.value)
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
const isVisualSearchTransferPrompt = (value) => {
  const text = String(value || '')
  return assistantFiles.value.length > 0 && /图片|图像|照片|附件|资料|上传|转交|交给|智能检索|观微|查看|分析/.test(text) && /智能检索|观微|查看|分析|什么问题|故障/.test(text)
}
const addFiles = async (event, target) => {
  const selected = Array.from(event.target.files || []).map(toFileMeta)
  if (target === 'search') {
    searchFiles.value.push(...selected.map((file) => ({ ...file, status: '已加入检索' })))
  } else if (target === 'assistant') {
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
  const isHighRisk = ['过热', '点火故障'].includes(searchForm.faultType)
  return {
    phenomenonSummary: `${searchForm.deviceModel || searchForm.deviceName} 出现${searchForm.faultType}现象，建议结合现场记录、图片和历史案例优先定位高频故障部位。`,
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
      { id: 'local-ref-1', title: `${searchForm.deviceModel || searchForm.deviceName} ${searchForm.faultType}历史故障案例`, type: '历史故障案例', category: '历史故障案例', equipment: searchForm.deviceName, model: searchForm.deviceModel, match: 86, summary: '同类现象常见于关键连接、润滑、散热或密封状态异常，需结合复测记录确认。', tags: [searchForm.faultType, '历史案例', '复检'] },
      { id: 'local-ref-2', title: `${searchForm.category}标准作业流程`, type: '标准作业流程 SOP', category: '标准作业流程 SOP', equipment: searchForm.deviceName, model: searchForm.deviceModel, match: 82, summary: '按安全确认、部位检查、处理记录、复测验收的顺序执行，保证后续沉淀可复用。', tags: ['SOP', searchForm.maintenanceLevel, '安全确认'] }
    ]
  }
}
const runSearch = async () => {
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
  nextTick(() => document.querySelector('.recheck-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
}
const previewTaskReport = (task) => { reportTask.value = task; selectedTask.value = null }
const windowPrint = () => window.print()
const saveRecheck = async (task) => {
  const form = recheckForms[task.id]
  let saved
  try { saved = await yixiuApi.recheck({ task_id: task.id, ...form, reviewer: user.name }) } catch (_error) {
    saved = { ...form, reviewer: user.name, reviewed_at: new Date().toISOString(), next_status: form.result === '通过' ? 'completed' : 'in_progress' }
  }
  task.recheck = saved
  task.status = saved.next_status
  task.current_step = saved.next_status === 'completed' ? '归档' : '返工整改'
  task.progress = saved.next_status === 'completed' ? 100 : 62
  toast('复检结果已保存')
}
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
    operatorMessages.value.push({
      id: `brief-${Date.now()}`,
      page: 'home',
      role: 'assistant',
      text: `今日共 ${tasks.value.length} 项任务，高风险 ${tasks.value.filter((task) => task.severity === 'high').length} 项，待复检 ${tasks.value.filter((task) => task.status === 'review').length} 项。建议先处理高风险和已逾期工单。`
    })
    return toast('今日检修简报已生成')
  }
  if (activePage.value === 'search') return runSearch()
  if (activePage.value === 'tasks') {
    taskPanel.value = 'manage'
    return toast('已打开任务管理')
  }
  if (activePage.value === 'knowledge') {
    knowledgePanel.value = 'files'
    return toast('已打开文件管理')
  }
  return runAudit()
}

const sendOperatorPrompt = async (prompt) => {
  const value = String(prompt || '').trim()
  if (!value && !assistantFiles.value.length) return
  if (value.includes('退出登录')) return logout()
  const sourcePage = activePage.value
  const visualTransferIntent = isVisualSearchTransferPrompt(value)
  const outgoingAttachments = snapshotFiles(assistantFiles.value)
  operatorMessages.value.push({ id: `user-${Date.now()}`, page: sourcePage, role: 'user', text: value || '请分析已上传的现场资料', attachments: outgoingAttachments, global: visualTransferIntent })
  operatorInput.value = ''
  if (visualTransferIntent) {
    try {
      await runTiangongLongTask(value || '请将现场图片交给观微进行智能检索和故障判断', sourcePage, { attachments: assistantFiles.value.slice() })
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
      operatorMessages.value.push({ id: `assistant-${Date.now()}`, page: sourcePage, role: 'assistant', text: `${response.response}\n引用：${(response.references || []).join('、')}` })
      // 附件缩略图仍需要显示在历史气泡中，稍后由页面退出统一释放 Blob URL。
      assistantFiles.value = []
      return toast('已完成图文联合分析')
    } catch (error) {
      return toast(error.message || '附件分析失败')
    }
  }
  if (isTiangongLongTaskPrompt(value)) {
    try {
      await runTiangongLongTask(value, sourcePage)
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
      operatorMessages.value.push({ id: `assistant-${Date.now()}`, page: sourcePage, role: 'assistant', text: `天工长任务启动失败：${aiosLive.error}` })
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
  if (value.includes('复检')) {
    activePage.value = 'tasks'
    taskPanel.value = 'recheck'
    return
  }
  if (value.includes('联系人')) {
    activePage.value = 'tasks'
    taskPanel.value = 'contacts'
    return
  }
  if (value.includes('文件管理')) {
    activePage.value = 'knowledge'
    knowledgePanel.value = 'files'
    return
  }
  if (value.includes('知识网络')) {
    activePage.value = 'knowledge'
    knowledgePanel.value = 'network'
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
  try {
    if (operatorProfile.value.id === 'tiangong') {
      const loadingMsg = { id: `loading-${Date.now()}`, page: sourcePage, role: 'assistant', text: '天工正在感知系统状态…', loading: true }
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
        await runTiangongLongTask(value, sourcePage)
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
      const cleanReply = reply.replace(/\[UI_PLAN\][\s\S]*?\[\/UI_PLAN\]/, '').trim()
      
      const uiCount = Array.isArray(uiPlan) && uiPlan.length ? uiPlan.filter((s) => s.action !== 'done').length : 0
      // 合并工具调用步骤和 UI 操作步骤
      const uiSteps = Array.isArray(uiPlan) && uiPlan.length
        ? uiPlan.filter((s) => s.action !== 'done').map((s) => ({ type: 'tool_call', tool: s.action, args: s, content: s.action === 'navigate' ? `→ ${TG_AGENT_NAMES[s.agent] || s.agent}` : (s.text || '') }))
        : steps
      
      // 替换 loading 消息为真实回复
      const loadIdx = operatorMessages.value.findIndex((m) => m.id === loadingMsg.id)
      const finalMsg = {
        id: loadIdx >= 0 ? loadingMsg.id : `assistant-${Date.now()}`,
        page: sourcePage,
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
    const response = await yixiuApi.assistantChat({ message: value, fileIds: [], agent: operatorProfile.value.name, page: sourcePage })
    operatorMessages.value.push({ id: `assistant-${Date.now()}`, page: sourcePage, role: 'assistant', text: response.response })
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

const stepLabel = (type) => ({ thought: '思考', action: '行动', tool_call: '工具', observation: '观察' }[type] || type)
const traceResult = (step) => {
  const r = step.tool_result
  if (!r) return ''
  return r.success ? `结果：${r.output}` : `失败：${r.error}`
}

const isTiangongLongTaskPrompt = (value) => {
  const text = String(value || '')
  const namesTiangong = operatorProfile.value.id === 'tiangong' || /天工|AIOS|总控/.test(text)
  const hasLongIntent = /长任务|执行|打开|查找|询问|问|总结|协作|知识库|摩托|可视化|UI_PLAN|十二步|12步|上传|转交|交给|图片|附件|图像/.test(text)
  const hasCrossAgentTarget = /知识库|智能检索|和鸣|观微|执矩|博闻|明鉴|摩托|CG-125|复检|联系人|沉淀|闭环|图片|附件|故障|什么问题/.test(text)
  if (namesTiangong && /可视化执行过程|UI_PLAN|12步|十二步/.test(text)) return true
  return hasLongIntent && hasCrossAgentTarget
}

const longTaskReplyText = (data) => {
  const steps = Array.isArray(data.steps) ? data.steps : []
  const body = steps.map((step, index) => `${index + 1}. ${step.agent}：${step.content}`).join('\n')
  return `${data.summary || '天工已完成长任务规划。'}${body ? `\n\n执行路径：\n${body}` : ''}`
}

const buildAiosReport = (data = {}, uiSteps = []) => {
  const digest = Array.isArray(data.step_digest) ? data.step_digest : Array.isArray(data.steps) ? data.steps : []
  const agents = [...new Set(digest.map((step) => step.agent || step.agent_id).filter(Boolean))]
  const readableAgents = agents.length ? agents.join('、') : '天工、观微、执矩、和鸣、博闻、明鉴'
  const highlights = digest.slice(0, 4).map((step) => step.content || step.expected_output || step.title).filter(Boolean)
  return {
    title: '设备检修闭环执行报告',
    subtitle: data.summary || '天工已完成本轮跨页面协同执行',
    conclusion: '已完成故障检索、任务联动、联系人协作、知识图谱定位与闭环报告生成；高风险与知识沉淀环节保留人工确认入口。',
    metrics: [
      { label: '执行步骤', value: `${uiSteps.length || digest.length || 0} 步` },
      { label: '协作智能体', value: `${agents.length || 6} 个` },
      { label: '业务页面', value: '5 个' },
      { label: '闭环状态', value: '待确认' }
    ],
    blocks: [
      {
        title: '已完成操作',
        items: [
          '完成多模态检索上下文整理，定位设备、型号、故障和资料依据。',
          '联动检修任务筛选，聚焦高风险、待复检和相关工单。',
          '向联系人会话写入协作消息，并保留后端会话记录。',
          '打开知识图谱与沉淀更新入口，准备形成可审核知识条目。'
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
        title: '关键结果',
        items: highlights.length ? highlights : [
          '已形成初步故障判断、检查位置、检测方式和安全注意事项。',
          '已生成检修闭环摘要，可继续导出为任务报告或知识沉淀。'
        ]
      },
      {
        title: '待人工确认',
        items: [
          '高风险步骤需现场负责人二次确认。',
          '知识入库前需核对引用依据、设备型号和复检结论。',
          '最终报告归档前建议补充现场图片与检测数据。'
        ]
      }
    ],
    tags: ['多智能体协作', '可视化执行', 'RAG 检索', '任务闭环', '知识沉淀']
  }
}

const runTiangongLongTask = async (value, sourcePage, options = {}) => {
  const transferAttachments = Array.isArray(options.attachments) ? options.attachments.filter(Boolean) : []
  const loadingMsg = { id: `loading-${Date.now()}`, page: sourcePage, role: 'assistant', text: '天工正在感知系统状态…', loading: true, global: transferAttachments.length > 0 }
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
    title: '生成 12 步执行计划',
    detail: '天工正在读取系统状态，并请求 AIOS 生成跨页面执行路线。',
    agentName: '天工',
    page: '首页 / AIOS',
    tool: 'aios.long-task',
    inputText: value,
    outputText: '等待后端返回 UI_PLAN。',
    current: 0,
    total: 12,
    progress: 4,
    steps: [
      { index: 1, label: '感知系统' },
      { index: 2, label: '生成计划' },
      { index: 3, label: '等待返回' }
    ]
  })
  const host = `http://${window.location.hostname || '127.0.0.1'}:5000`
  const taskPayload = await fetch(`${host}/api/yixiu/aios/long-task`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ goal: value })
  }).then(r => r.json().catch(() => ({})))

  const data = taskPayload.data || taskPayload || {}
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
      ...uiPlan.filter((step) => !['navigate'].includes(step.action) || step.page !== '首页')
    ].map((step, index) => ({ ...step, index: index + 1 }))
  }
  applyAiosRun(data, Array.isArray(data.events) ? data.events : [])
  const uiSteps = uiPlan.filter((s) => s.action !== 'done').map((s) => ({
    type: 'tool_call',
    tool: s.mcpTool || s.tool || s.action,
    args: s,
    content: s.action === 'navigate'
      ? `→ ${s.page || TG_AGENT_NAMES[s.agent] || s.agent}`
      : (s.input?.query || s.input?.keyword || s.keyword || s.text || s.reason || s.expected || '')
  }))
  const loadIdx = operatorMessages.value.findIndex((m) => m.id === loadingMsg.id)
  const finalMsg = {
    id: loadIdx >= 0 ? loadingMsg.id : `assistant-${Date.now()}`,
    page: sourcePage,
    role: 'assistant',
    text: longTaskReplyText(data),
    report: buildAiosReport(data, uiSteps),
    steps: uiSteps,
    toolCalls: uiSteps.length,
    global: transferAttachments.length > 0
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
  mingjian: { page: 'tasks', panel: 'recheck' },
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
  page: '首页',
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
const tgSleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

const tgActionLabel = (step) => {
  const action = step?.action
  if (action === 'navigate') return `进入${step.page || TG_AGENT_NAMES[step.agent] || '模块'}`
  if (action === 'search' || action === 'knowledge_search') return '智能检索'
  if (action === 'filter') return '筛选工单'
  if (action === 'openPanel') return `打开${step.page || '板块'}`
  if (action === 'openKnowledgeGraph') return '打开图谱'
  if (action === 'openChat') return '联系人协作'
  if (action === 'summarize') return '整理记忆'
  if (action === 'approve') return '等待确认'
  if (action === 'report') return '生成报告'
  if (action === 'finish') return '完成闭环'
  if (action === 'type') return '填写指令'
  if (action === 'click_send') return '发送请求'
  if (action === 'agent_type') return '输入智能体消息'
  if (action === 'agent_send') return '发送给智能体'
  if (action === 'transfer_attachment') return '转交现场图片'
  if (action === 'contact_type') return '输入协作消息'
  if (action === 'contact_send') return '发送给联系人'
  if (action === 'wait') return '等待响应'
  return '执行操作'
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
  if (text.includes('智能检索')) return 'search'
  if (text.includes('知识库') || text.includes('知识图谱') || text.includes('沉淀')) return 'knowledge'
  if (text.includes('检修任务') || text.includes('联系人') || text.includes('复检')) return 'tasks'
  if (text.includes('个人中心')) return 'profile'
  if (text.includes('首页') || text.includes('报告预览')) return 'home'
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
    if (knowledgePanel.value === 'files') return `文件管理已打开，当前资料 ${files.value.length} 份。`
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
  return expanded
}

const tgApplyStepState = async (step = {}) => {
  const page = tgPageKey(step)
  const action = step.action
  const input = step.input || {}
  const keyword = input.query || input.keyword || step.keyword || step.text || 'CG-125 发动机异响'
  const agent = step.agent || ''

  selectedAgentId.value = agent || selectedAgentId.value
  activePage.value = page

  if (page === 'search') {
    searchPanel.value = action === 'summarize' ? 'history' : 'multimodal'
    if (keyword) {
      searchForm.query = String(keyword)
      searchForm.deviceModel = input.model || searchForm.deviceModel || 'CG-125'
      searchForm.deviceName = input.deviceName || searchForm.deviceName || '摩托车发动机总成'
      searchForm.faultCode = input.faultCode || searchForm.faultCode || 'NOISE-02'
      searchForm.faultType = input.faultType || searchForm.faultType || '异响'
    }
  }

  if (page === 'tasks') {
    if (String(step.page || step.target || '').includes('联系人')) taskPanel.value = 'contacts'
    else if (String(step.page || step.target || '').includes('复检')) taskPanel.value = 'recheck'
    else taskPanel.value = 'manage'
    if (taskFilters.keyword !== undefined) taskFilters.keyword = keyword
  }

  if (page === 'knowledge') {
    if (String(step.page || step.target || '').includes('沉淀')) knowledgePanel.value = 'update'
    else if (action === 'openKnowledgeGraph' || String(step.page || step.target || '').includes('图谱')) knowledgePanel.value = 'network'
    else knowledgePanel.value = 'library'
    knowledgeKeyword.value = keyword
    if (knowledgePanel.value === 'network') window.setTimeout(settleGraphChart, 120)
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
    .map((item, stepIndex) => ({ index: stepIndex + 1, label: tgActionLabel(item) }))
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

async function tgTypeAgentMessage(text) {
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
  operatorMessages.value.push({ id: `user-${Date.now()}`, page: sourcePage, role: 'user', text: value })
  operatorInput.value = ''
  try {
    if (agentId && agentId !== 'tiangong' && agentProfileMap[agentId]) {
      const response = await yixiuApi.invokeAgent(agentId, { goal: value, message: value, commit: true })
      const result = response.result || response
      const agentName = response.agent?.name || agentProfile.name || TG_AGENT_NAMES[agentId] || '智能体'
      operatorMessages.value.push({
        id: `assistant-${Date.now()}`,
        page: sourcePage,
        role: 'assistant',
        text: `${agentName}已接收天工分派：${result.summary || '已完成本次协作处理。'}`
      })
      return
    }
    const response = await yixiuApi.assistantChat({ message: value, fileIds: [], agent: agentProfile.name, page: sourcePage })
    operatorMessages.value.push({ id: `assistant-${Date.now()}`, page: sourcePage, role: 'assistant', text: response.response })
  } catch (error) {
    operatorMessages.value.push({ id: `assistant-${Date.now()}`, page: sourcePage, role: 'assistant', text: `（${agentProfile.name || '智能体'}暂未响应：${error.message || ''}）` })
  }
}

async function tgClickSend(step = {}) {
  const btn = pickVisibleElement('.operator-panel .ask-box button[type="submit"], .floating-ask-box button[type="submit"], .ask-box button[type="submit"]')
  const inputEl = pickVisibleElement('.operator-panel .ask-box input, .floating-ask-box input, .ask-box input')
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
  const keyword = step.input?.keyword || step.text || operatorInput.value || '现场图片故障识别'
  searchForm.query = `${keyword}；请结合上传图片判断现场设备或道路积水相关风险。`
  searchForm.deviceName = searchForm.deviceName || '现场待确认设备'
  searchForm.deviceModel = searchForm.deviceModel || '待确认型号'
  searchForm.faultType = searchForm.faultType || '现场异常'
  const existing = new Set(searchFiles.value.map((file) => file.localId || file.name))
  const incoming = attachments
    .filter((file) => !existing.has(file.localId || file.name))
    .map(cloneAssistantFileForSearch)
  if (incoming.length) searchFiles.value.push(...incoming)
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
  tgRunUi.decision = '根据用户目标选择页面、智能体和工具顺序'
  tgRunUi.check = '尚未开始校验'
  tgRunUi.steps = steps.filter((item) => item.action !== 'done').map((item, index) => ({ index: index + 1, label: tgActionLabel(item) }))
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
          await tgTypeAgentMessage(step.text || '')
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
.profile-setting-list button, .profile-preference-list button { min-height: 42px; display: grid; grid-template-columns: 22px 82px minmax(0, 1fr) auto; gap: 10px; align-items: center; border: 0; border-bottom: 1px solid #edf2f4; border-radius: 0; background: transparent; color: #536670; text-align: left; }
.profile-setting-list button:last-child, .profile-preference-list button:last-child { border-bottom: 0; }
.profile-setting-list .ui-icon, .profile-preference-list .ui-icon { width: 17px; height: 17px; color: #5f86a7; }
.profile-setting-list b, .profile-preference-list b { color: #3a4d57; font-size: 13px; font-weight: 720; }
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
.profile-growth-benefits { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.profile-growth-benefits span { display: grid; place-items: center; gap: 8px; min-height: 68px; border-radius: 14px; background: rgba(255,255,255,.12); color: #edf5ff; font-size: 12px; }
.profile-growth-benefits .ui-icon { width: 22px; height: 22px; color: #d9c07a; }
.profile-preference-list button { grid-template-columns: 22px minmax(0, 1fr) auto; }
.profile-preference-list span { color: #7a8991; font-size: 12px; }
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
  grid-template-rows: minmax(238px, auto) 166px;
  align-items: stretch;
}
.profile-focus-shell .profile-panel { min-height: 0; height: 100%; }
.profile-focus-shell .profile-security-panel,
.profile-focus-shell .profile-tools-panel,
.profile-focus-shell .profile-activity-panel { min-height: 238px; }
.profile-focus-shell .profile-growth-card,
.profile-focus-shell .profile-preference-panel { min-height: 166px; height: 166px; }
.profile-focus-shell .profile-growth-card {
  grid-template-columns: minmax(260px, .75fr) minmax(160px, .35fr) minmax(360px, .9fr);
  gap: 20px;
  padding: 18px 24px;
}
.profile-focus-shell .profile-growth-card p { margin-bottom: 6px; }
.profile-focus-shell .profile-growth-card h3 { font-size: 34px; line-height: 1; }
.profile-focus-shell .profile-growth-card i { margin-top: 12px; }
.profile-focus-shell .profile-growth-benefits { align-items: center; gap: 10px; }
.profile-focus-shell .profile-growth-benefits span { min-height: 58px; }
.profile-focus-shell .profile-preference-panel { padding: 16px 18px; }
.profile-focus-shell .profile-preference-panel .profile-panel-head { margin-bottom: 8px; }
.profile-focus-shell .profile-preference-list { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.profile-focus-shell .profile-preference-list button {
  min-height: 42px;
  grid-template-columns: 20px minmax(0, 1fr) auto;
  padding: 0 10px;
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
.kb-template-card { display: grid; grid-template-columns: 44px 1fr auto; gap: 12px; align-items: center; padding: 14px; border: 1px solid #e5ebec; border-radius: 10px; cursor: pointer; transition: all .15s; background: #fff; }
.kb-template-card:hover { border-color: #176f69; box-shadow: 0 4px 14px rgba(23,111,105,.1); }
.kb-template-icon { width: 44px; height: 44px; border-radius: 10px; background: #f0f4f4; display: grid; place-items: center; font-size: 22px; }
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
.search-agent-tools { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
.search-agent-tools button {
  min-height: 70px;
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  padding: 14px 16px;
  border: 1px solid #e0eaeb;
  border-radius: 16px;
  background: #fff;
  color: #294f54;
  text-align: left;
  box-shadow: 0 9px 18px rgba(31,69,75,.045);
}
.search-agent-tools button:hover { border-color: #b9d7d2; background: #f7fbfa; transform: translateY(-1px); }
.search-agent-tools .ui-icon { width: 25px; height: 25px; justify-self: center; color: #2f7f8f; }
.search-agent-tools span { display: grid; gap: 4px; min-width: 0; }
.search-agent-tools b { color: #263d42; font-size: 14px; }
.search-agent-tools small { color: #738688; font-size: 11px; }
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
  object-fit: cover;
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
.tg-run-card { overflow: hidden; border: 1px solid rgba(193,208,204,.86); border-radius: 20px; background: linear-gradient(180deg, rgba(255,255,253,.98), rgba(248,250,247,.96)); box-shadow: 0 20px 46px rgba(36,62,63,.16), 0 1px 0 rgba(255,255,255,.96) inset; backdrop-filter: blur(18px); animation: tg-run-in .26s ease-out; }
@keyframes tg-run-in { from { opacity: 0; transform: translate3d(0,-12px,0) scale(.98); } to { opacity: 1; transform: translate3d(0,0,0) scale(1); } }
.tg-run-card header { display: grid; grid-template-columns: 54px minmax(0,1fr) auto; align-items: center; gap: 13px; padding: 14px 16px 10px; }
.tg-run-mark { position: relative; width: 54px; height: 54px; display: grid; place-items: center; border-radius: 50%; background: linear-gradient(145deg, #fffdf8, #edf4ef); border: 1px solid rgba(198,214,207,.95); box-shadow: 0 12px 24px rgba(35,95,99,.14), 0 0 0 6px rgba(238,244,239,.78); }
.tg-run-mark img { width: 46px; height: 46px; border-radius: 50%; object-fit: cover; display: block; background: #f4f8f6; }
.tg-run-mark i { position: absolute; right: 2px; bottom: 4px; width: 12px; height: 12px; border-radius: 50%; background: #6aa876; border: 2px solid #fff; box-shadow: 0 0 0 3px rgba(106,168,118,.16); }
.tg-run-card small { display: block; margin-bottom: 3px; color: #758887; font-size: 11px; font-weight: 800; }
.tg-run-card b { display: block; overflow: hidden; color: #17393b; font-size: 15px; text-overflow: ellipsis; white-space: nowrap; }
.tg-run-card em { min-width: 54px; padding: 6px 10px; border-radius: 999px; background: #f5efe4; color: #8a662d; font-size: 12px; font-style: normal; font-weight: 900; text-align: center; }
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

.knowledge-focus-shell .page-scroll {
  overflow: hidden !important;
  padding: 10px 12px 12px !important;
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
.search-focus-shell .search-agent-tools {
  gap: 10px;
}
.search-focus-shell .search-agent-tools button {
  min-height: 58px;
  padding: 10px 12px;
  border-radius: 13px;
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

</style>
