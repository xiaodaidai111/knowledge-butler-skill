import {
  createOverviewFromMock,
  mockAgents,
  mockContacts,
  mockFiles,
  mockKnowledge,
  mockSearchResult,
  mockTasks
} from '../data/yixiuMock.js'

const getHost = () => {
  if (typeof window === 'undefined') return 'http://127.0.0.1:5000'
  return `http://${window.location.hostname || '127.0.0.1'}:5000`
}

const API_BASE = `${getHost()}/api/yixiu`
const SYSTEM_BASE = getHost()

const getStoredToken = () => {
  if (typeof window !== 'undefined') {
    const token = window.localStorage?.getItem('token') || window.localStorage?.getItem('yixiu-token')
    if (token) return token
  }
  try {
    if (typeof uni !== 'undefined' && uni.getStorageSync) return uni.getStorageSync('token') || ''
  } catch (_error) {
    return ''
  }
  return ''
}

const operationId = (prefix = 'op') => `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2, 10)}`

const normalizeResponse = async (response) => {
  const payload = await response.json().catch(() => ({}))
  if (!response.ok || (payload.code && payload.code >= 400)) {
    throw new Error(payload.message || `请求失败：${response.status}`)
  }
  return payload.data ?? payload
}

export const requestJson = async (path, options = {}) => {
  const token = getStoredToken()
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers
  }
  const response = await fetch(`${API_BASE}${path}`, {
    method: options.method || 'GET',
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined
  })
  return normalizeResponse(response)
}

const confirmedBody = (payload = {}, prefix = 'aios') => {
  const idempotencyKey = payload.idempotency_key || operationId(prefix)
  return {
    body: { ...payload, confirmed: payload.confirmed ?? true, idempotency_key: idempotencyKey },
    headers: { 'Idempotency-Key': idempotencyKey }
  }
}

const resolveAssetUrl = (url) => {
  if (!url || url.startsWith('blob:') || url.startsWith('data:') || /^https?:/i.test(url)) return url
  return `${getHost()}${url.startsWith('/') ? '' : '/'}${url}`
}

const normalizeFile = (file) => ({ ...file, url: resolveAssetUrl(file.url) })

const knowledgeTypes = ['维修手册', '历史故障案例', '标准作业流程 SOP', '安全操作规范']

const inferKnowledgeType = (item = {}) => {
  const text = [
    item.type,
    item.category,
    item.title,
    item.name,
    item.source,
    item.chapter,
    item.summary,
    ...(Array.isArray(item.tags) ? item.tags : []),
    ...(Array.isArray(item.keywords) ? item.keywords : [])
  ].filter(Boolean).join(' ')

  if (/安全|规范|规程|作业许可|挂牌|隔离/.test(text)) return '安全操作规范'
  if (/SOP|标准作业|作业流程|检修流程|操作流程/.test(text)) return '标准作业流程 SOP'
  if (/案例|故障记录|经验|复盘|处置记录/.test(text)) return '历史故障案例'
  return '维修手册'
}

const supplementMissingKnowledgeTypes = (items) => {
  const result = [...items]
  const existingKeys = new Set(result.map((item) => `${item.id || ''}|${item.title || ''}`))
  knowledgeTypes.forEach((type) => {
    if (result.some((item) => item.type === type)) return
    const fallback = mockKnowledge.find((item) => inferKnowledgeType(item) === type)
    const key = fallback ? `${fallback.id || ''}|${fallback.title || ''}` : ''
    if (fallback && !existingKeys.has(key)) {
      result.push({ ...fallback, type, category: type })
      existingKeys.add(key)
    }
  })
  return result
}

export const yixiuApi = {
  async overview() {
    try {
      const data = await requestJson('/overview')
      const fallback = createOverviewFromMock()
      return {
        ...fallback,
        serverOverview: data,
        stats: {
          ...fallback.stats,
          pending: data.stats?.pending_tasks ?? fallback.stats.pending,
          highRisk: data.stats?.high_risk_items ?? fallback.stats.highRisk,
          knowledgeTotal: data.stats?.knowledge_items ?? fallback.stats.knowledgeTotal,
          ...data.stats
        },
        agents: data.agents?.length ? data.agents : mockAgents,
        tasks: data.tasks?.length ? data.tasks.map((task, index) => ({ ...mockTasks[index % mockTasks.length], ...task })) : mockTasks,
        knowledge: data.knowledge?.length ? data.knowledge : mockKnowledge
      }
    } catch (error) {
      return { ...createOverviewFromMock(), fallbackReason: error.message }
    }
  },

  async health() {
    try {
      const response = await fetch(`${SYSTEM_BASE}/api/system/health`)
      const data = await normalizeResponse(response)
      return { system: '正常', backend: '在线', ai: '按配置启用', rag: '可用性自动检测', knowledge: '资料库在线', detail: data }
    } catch (_error) {
      return { system: '异常', backend: '离线', ai: '待确认', rag: '待确认', knowledge: `${mockKnowledge.length} 条本地资料` }
    }
  },

  async agents(agentId = '') {
    try {
      const params = agentId ? `?agent_id=${encodeURIComponent(agentId)}` : ''
      const data = await requestJson(`/agents${params}`)
      return data.agents?.length ? data.agents : mockAgents
    } catch (_error) {
      return agentId ? mockAgents.filter((agent) => agent.id === agentId || agent.name === agentId) : mockAgents
    }
  },

  createSession(payload = {}) {
    return requestJson('/session', { method: 'POST', body: payload })
  },

  invokeAgent(agentId, payload = {}) {
    return requestJson(`/agents/${encodeURIComponent(agentId)}/invoke`, { method: 'POST', body: payload })
  },

  dispatchAgents(payload = {}) {
    return requestJson('/agents/dispatch', { method: 'POST', body: payload })
  },

  aiosPlan(payload = {}) {
    return requestJson('/aios/plan', { method: 'POST', body: payload })
  },

  aiosExecute(payload = {}) {
    const options = confirmedBody(payload, 'aios-execute')
    return requestJson('/aios/execute', { method: 'POST', ...options })
  },

  aiosStatus(limit = 10) {
    return requestJson(`/aios/status?limit=${encodeURIComponent(limit)}`)
  },

  aiosRunDetail(runId) {
    return requestJson(`/aios/runs/${encodeURIComponent(runId)}`)
  },

  aiosEvents(params = {}) {
    const query = new URLSearchParams()
    if (params.runId) query.set('run_id', params.runId)
    if (params.agentId) query.set('agent_id', params.agentId)
    if (params.limit) query.set('limit', params.limit)
    return requestJson(`/aios/events${query.size ? `?${query}` : ''}`)
  },

  aiosResume(payload = {}) {
    const options = confirmedBody(payload, 'aios-resume')
    return requestJson('/aios/resume', { method: 'POST', ...options })
  },

  databaseStatus() {
    return requestJson('/database/status')
  },

  databaseBootstrap() {
    return requestJson('/database/bootstrap', { method: 'POST', body: {} })
  },

  async tasks(filters = {}) {
    try {
      const params = new URLSearchParams()
      if (filters.status && filters.status !== 'all') params.set('status', filters.status)
      const data = await requestJson(`/tasks${params.size ? `?${params}` : ''}`)
      const rows = data.tasks?.length ? data.tasks : mockTasks
      return rows.map((task, index) => ({ ...mockTasks[index % mockTasks.length], ...task }))
    } catch (_error) {
      return filters.status && filters.status !== 'all' ? mockTasks.filter((task) => task.status === filters.status) : mockTasks
    }
  },

  createTask(task) {
    const options = confirmedBody(task, 'task-create')
    return requestJson('/tasks', { method: 'POST', ...options })
  },

  updateTaskStatus(taskId, status, extra = {}) {
    return requestJson(`/tasks/${taskId}/status`, { method: 'PUT', body: { status, ...extra } })
  },

  completeTaskStep(taskId, stepIndex, payload = {}) {
    return requestJson(`/tasks/${taskId}/steps/${stepIndex}`, { method: 'PUT', body: { completed: true, ...payload } })
  },

  async search(payload) {
    const data = await requestJson('/search', { method: 'POST', body: payload })
    const manuals = (data.matched_manuals || []).map((item, index) => {
      const type = inferKnowledgeType(item)
      return {
      id: item.id || `manual-${index}`,
      title: item.title || item.name || '设备检修资料',
      type,
      category: type,
      equipment: item.equipment || payload.deviceName || '检修设备',
      model: item.model || data.device_model || payload.deviceModel,
      match: item.match || Math.max(75, Number(data.match_score || 88) - index * 3),
      updated_at: item.updated_at || '2026-08-04',
      source: item.source || item.chapter || '知识库',
      summary: item.summary || item.content || '与当前故障和设备型号相关的检修依据。',
      tags: item.tags || ['设备检修', '检索召回'],
      citations: item.citations || 1,
      fileType: item.fileType || 'DOC'
      }
    })
    const references = supplementMissingKnowledgeTypes(manuals.length ? manuals : mockKnowledge)
    return {
      ...mockSearchResult,
      phenomenonSummary: data.phenomenon_summary || `${payload.deviceModel || ''} ${payload.faultType || ''}联合检索结果`,
      query: data.query || payload.query,
      device_model: data.device_model || payload.deviceModel,
      confidence: Number(data.match_score || mockSearchResult.confidence),
      risk: data.risk || mockSearchResult.risk,
      stopAdvice: data.stop_advice || mockSearchResult.stopAdvice,
      causes: data.causes?.length ? data.causes : mockSearchResult.causes,
      positions: data.positions?.length ? data.positions : mockSearchResult.positions,
      tools: data.tools?.length ? data.tools : mockSearchResult.tools,
      modalities: data.modalities || ['text'],
      visualFindings: data.visual_findings || [],
      attachments: (data.attachments || []).map(normalizeFile),
      references,
      suggestion: {
        ...mockSearchResult.suggestion,
        steps: (data.recommended_sop || []).map((step) => typeof step === 'string' ? step : step.title),
        stepDetails: data.recommended_sop || [],
        risks: data.safety || mockSearchResult.suggestion.risks
      },
      audit: data.audit || {}
    }
  },

  async knowledge(keyword = '') {
    try {
      const data = await requestJson(`/knowledge${keyword ? `?keyword=${encodeURIComponent(keyword)}` : ''}`)
      return data.items?.length ? data.items : mockKnowledge
    } catch (_error) {
      return keyword ? mockKnowledge.filter((item) => JSON.stringify(item).includes(keyword)) : mockKnowledge
    }
  },

  async files() {
    try {
      const data = await requestJson('/files')
      return data.files?.length ? data.files.map(normalizeFile) : mockFiles
    } catch (_error) {
      return mockFiles
    }
  },

  async uploadFile(rawFile, meta = {}, onProgress) {
    if (!(rawFile instanceof File)) throw new Error('缺少原始文件内容')
    const form = new FormData()
    form.append('file', rawFile, rawFile.name)
    Object.entries(meta).forEach(([key, value]) => form.append(key, value ?? ''))
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      xhr.open('POST', `${API_BASE}/files`)
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable && onProgress) onProgress(Math.round(event.loaded / event.total * 100))
      }
      xhr.onerror = () => reject(new Error('文件上传失败，请检查后端服务连接'))
      xhr.onload = async () => {
        try {
          const payload = JSON.parse(xhr.responseText || '{}')
          if (xhr.status < 200 || xhr.status >= 300 || (payload.code && payload.code >= 400)) throw new Error(payload.message || `上传失败：${xhr.status}`)
          resolve(normalizeFile(payload.data ?? payload))
        } catch (error) {
          reject(error)
        }
      }
      xhr.send(form)
    })
  },

  async contacts() {
    try {
      const data = await requestJson('/contacts')
      return data.contacts?.length ? data.contacts : mockContacts
    } catch (_error) {
      return mockContacts
    }
  },

  upsertContact(contact) {
    return requestJson(`/contacts/${encodeURIComponent(contact.id)}`, { method: 'PUT', body: contact })
  },

  async conversationMessages(conversationId) {
    const data = await requestJson(`/conversations/${encodeURIComponent(conversationId)}/messages`)
    return data.messages || []
  },

  sendConversationMessage(conversationId, payload) {
    const options = confirmedBody(payload, 'conversation-message')
    return requestJson(`/conversations/${encodeURIComponent(conversationId)}/messages`, { method: 'POST', ...options })
  },

  recheck(payload) {
    return requestJson('/recheck', { method: 'POST', body: payload })
  },

  updateKnowledge(payload) {
    const options = confirmedBody(payload, 'knowledge-update')
    return requestJson('/knowledge/update', { method: 'POST', ...options })
  },

  reviewKnowledge(itemId, payload) {
    return requestJson(`/knowledge/${itemId}/review`, { method: 'PUT', body: payload })
  },

  assistantChat(payload) {
    return requestJson('/assistant/chat', { method: 'POST', body: payload })
  },

  audit(payload) {
    return requestJson('/audit', { method: 'POST', body: payload })
  },

  saveKnowledgeContent(itemId, payload) {
    return requestJson(`/knowledge/${itemId}/content`, { method: 'PUT', body: payload })
  },
  knowledgeVersions(itemId) {
    return requestJson(`/knowledge/${itemId}/versions`)
  },
  restoreKnowledgeVersion(itemId, versionId) {
    return requestJson(`/knowledge/${itemId}/versions/${versionId}/restore`, { method: 'POST', body: {} })
  },
  knowledgeLinks(itemId) {
    return requestJson(`/knowledge/${itemId}/links`)
  },
  addKnowledgeLink(itemId, payload) {
    return requestJson(`/knowledge/${itemId}/links`, { method: 'POST', body: payload })
  },
  removeKnowledgeLink(itemId, linkId) {
    return requestJson(`/knowledge/${itemId}/links/${linkId}`, { method: 'DELETE' })
  },
  linkedKnowledge(linkType, targetId) {
    return requestJson(`/knowledge/linked/${linkType}/${encodeURIComponent(targetId)}`)
  },
  knowledgeCollaborators(itemId) {
    return requestJson(`/knowledge/${itemId}/collaborators`)
  },
  addKnowledgeCollaborator(itemId, payload) {
    return requestJson(`/knowledge/${itemId}/collaborators`, { method: 'POST', body: payload })
  },
  templates(keyword = '') {
    return requestJson(`/templates${keyword ? `?keyword=${encodeURIComponent(keyword)}` : ''}`)
  },
  createTemplate(payload) {
    return requestJson('/templates', { method: 'POST', body: payload })
  },
  deleteTemplate(id) {
    return requestJson(`/templates/${id}`, { method: 'DELETE' })
  }
}
