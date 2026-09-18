import { init, use } from 'echarts/core'
import { BarChart, GraphChart, LineChart, PieChart, RadarChart } from 'echarts/charts'
import {
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  MarkLineComponent,
  MarkPointComponent,
  TitleComponent,
  TooltipComponent,
  TransformComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

// 只注册一休实际使用的图表与组件。保留 ECharts 6 的完整交互和动画能力，
// 避免公网构建把未使用的 3D、地图、仪表盘等模块一并打进首屏包。
use([
  BarChart,
  GraphChart,
  LineChart,
  PieChart,
  RadarChart,
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  MarkLineComponent,
  MarkPointComponent,
  TitleComponent,
  TooltipComponent,
  TransformComponent,
  CanvasRenderer
])

export { init }
