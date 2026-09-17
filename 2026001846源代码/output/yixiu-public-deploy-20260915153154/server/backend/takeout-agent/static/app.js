const chatWindow = document.getElementById('chat-window');
const chatForm = document.getElementById('chat-form');
const chatText = document.getElementById('chat-text');
const chatImageInput = document.getElementById('chat-image-input');
const apiKeyInput = document.getElementById('api-key');
const apiBaseUrlInput = document.getElementById('api-base-url');
const restaurantGrid = document.getElementById('restaurant-grid');
const avgScore = document.getElementById('avg-score');
const riskCount = document.getElementById('risk-count');
const topRisk = document.getElementById('top-risk');
const summaryTime = document.getElementById('summary-time');
const statTotal = document.getElementById('stat-total');
const statRiskRate = document.getElementById('stat-risk-rate');
const statTrend = document.getElementById('stat-trend');

const SHOW_DEBUG = false;

const history = [];
// 最近一次图片分析结果，用于对话接口的 context，让智能体能结合上下文与用户交流
let lastImageAnalysis = null;
// 最近一次查看的店铺（可从店铺画像点击或单店评分得到），用于对话 context
let lastRestaurant = null;

const scoreColor = (score) => {
  if (score >= 85) return '#2d8c70';
  if (score >= 70) return '#e2b34b';
  if (score >= 55) return '#e2843a';
  return '#d46a57';
};

const getApiHeaders = () => {
  const headers = {};
  const apiKey = apiKeyInput?.value?.trim();
  const baseUrl = apiBaseUrlInput?.value?.trim();
  if (apiKey) headers['X-Api-Key'] = apiKey;
  if (baseUrl) headers['X-Base-Url'] = baseUrl;
  return headers;
};

const renderSummary = (summary, restaurants = []) => {
  avgScore.textContent = summary.avg_score ?? '--';
  riskCount.textContent = summary.high_risk_count ?? '--';
  topRisk.textContent = summary.top_risk ?? '--';
  summaryTime.textContent = `更新 ${new Date(summary.updated_at).toLocaleString('zh-CN')}`;

  const total = restaurants.length;
  if (statTotal) statTotal.textContent = total ? total : '--';

  if (statRiskRate) {
    const rate = total ? Math.round((summary.high_risk_count / total) * 100) : 0;
    statRiskRate.textContent = total ? `${rate}%` : '--';
  }

  if (statTrend) {
    const score = Number(summary.avg_score) || 0;
    let trend = '未知';
    if (score >= 85) trend = '优秀';
    else if (score >= 70) trend = '稳健';
    else if (score >= 55) trend = '预警';
    else trend = '高风险';
    statTrend.textContent = total ? trend : '--';
  }
};

const createRestaurantCard = (store) => {
  const wrapper = document.createElement('div');
  wrapper.className = 'restaurant-card';

  const ringValue = `${store.hygiene_score}%`;
  const ringColor = scoreColor(store.hygiene_score);

  const tags = [
    store.category ? `<span class="tag">${store.category}</span>` : '',
    store.rating != null ? `<span class="tag">评分 ${store.rating}</span>` : '',
    store.last_inspection_score != null ? `<span class="tag">巡检 ${store.last_inspection_score}</span>` : '',
    store.price_range ? `<span class="tag">客单 ${store.price_range}</span>` : '',
  ]
    .filter(Boolean)
    .join('');

  const foot = [
    store.monthly_orders != null ? `<span>月单 ${store.monthly_orders}</span>` : '',
    store.complaint_count != null ? `<span>投诉 ${store.complaint_count}</span>` : '',
    store.violations != null ? `<span>违规 ${store.violations}</span>` : '',
  ]
    .filter(Boolean)
    .join('');

  wrapper.innerHTML = `
    <div class="restaurant-meta">
      <div>
        <h3>${store.name}</h3>
        <div class="tags">${tags}</div>
      </div>
      <div class="score-stack">
        <div class="score-ring" style="--ring-color:${ringColor}; --ring-value:${ringValue}">
          <span>${store.hygiene_grade}</span>
        </div>
        <div class="score-number">${store.hygiene_score}</div>
      </div>
    </div>
    <div class="tags">
      ${store.risk_tags.map((tag) => `<span class="tag">${tag}</span>`).join('')}
    </div>
    <div class="section-lead">${store.summary}</div>
    <div class="restaurant-foot">${foot}</div>
  `;

  return wrapper;
};

// 统一解析接口返回：支持 { code, message, data } 格式，成功时用 data；兼容无 code 的旧格式
const parseApiResponse = (res) => {
  if (res.code === 0 && res.data != null) return res.data;
  if (res.data != null) return res.data;
  return res;
};

const loadRestaurants = async () => {
  const response = await fetch('/api/demo/analyze');
  const res = await response.json();
  const data = parseApiResponse(res);
  renderSummary(data.summary, data.restaurants || []);
  restaurantGrid.innerHTML = '';
  (data.restaurants || []).forEach((store) => {
    restaurantGrid.appendChild(createRestaurantCard(store));
  });
};

const addMessage = (target, role, text, sources = [], imageUrl = '', meta = '') => {
  const message = document.createElement('div');
  message.className = `message ${role}`;
  const content = document.createElement('div');
  content.textContent = text;
  message.appendChild(content);

  if (imageUrl) {
    const preview = document.createElement('img');
    preview.src = imageUrl;
    preview.alt = '上传的照片预览';
    preview.className = 'image-preview';
    message.appendChild(preview);
  }

  if (SHOW_DEBUG && sources.length) {
    const sourceBox = document.createElement('div');
    sourceBox.className = 'sources';
    sourceBox.textContent = `知识源：${sources.join('、')}`;
    message.appendChild(sourceBox);
  }

  if (SHOW_DEBUG && meta) {
    const metaBox = document.createElement('div');
    metaBox.className = 'sources';
    metaBox.textContent = meta;
    message.appendChild(metaBox);
  }

  target.appendChild(message);
  target.scrollTop = target.scrollHeight;
};

const readFileAsDataUrl = (file) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error('read failed'));
    reader.readAsDataURL(file);
  });

const sendChat = async (text, imageFile) => {
  const userContent = text || (imageFile ? '[发了一张外卖图]' : '');
  history.push({ role: 'user', content: userContent });
  let imageUrl = '';
  if (imageFile) {
    imageUrl = await readFileAsDataUrl(imageFile);
    addMessage(chatWindow, 'user', text || '[一张外卖图]', [], imageUrl);
  } else {
    addMessage(chatWindow, 'user', text);
  }

  let response;
  if (imageFile) {
    const formData = new FormData();
    formData.append('message', text || '');
    formData.append('history', JSON.stringify(history.slice(0, -1)));
    formData.append('image', imageFile);
    response = await fetch('/api/chat', {
      method: 'POST',
      headers: getApiHeaders(),
      body: formData,
    });
  } else {
    const body = { message: text, history };
    if (lastImageAnalysis || lastRestaurant) {
      body.context = {};
      if (lastImageAnalysis) body.context.last_image_analysis = lastImageAnalysis;
      if (lastRestaurant) body.context.last_restaurant = lastRestaurant;
    }
    response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getApiHeaders() },
      body: JSON.stringify(body),
    });
  }

  const res = await response.json();
  const data = parseApiResponse(res);
  const reply = data.reply || res.message || '请稍后重试。';
  history.push({ role: 'assistant', content: reply });
  if (data.image_analysis) lastImageAnalysis = data.image_analysis;
  if (data.restaurant) lastRestaurant = data.restaurant;
  const meta = data.error
    ? `模式：${data.mode || 'unknown'} | 错误：${data.error}`
    : data.mode
      ? `模式：${data.mode}`
      : '';
  addMessage(chatWindow, 'assistant', reply, data.sources || [], '', meta);
};

chatForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const text = chatText.value.trim();
  const imageFile = chatImageInput && chatImageInput.files && chatImageInput.files[0];
  if (!text && !imageFile) return;
  chatText.value = '';
  if (chatImageInput) chatImageInput.value = '';
  sendChat(text, imageFile || null);
});

const initAnimations = () => {
  const items = document.querySelectorAll('[data-animate]');
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.2 }
  );

  items.forEach((item) => observer.observe(item));
};

loadRestaurants();
initAnimations();
addMessage(chatWindow, 'assistant', '你好，我是慧识外卖小助手。告诉我店名或发一张外卖图，我帮你评估卫生和包装风险。');
