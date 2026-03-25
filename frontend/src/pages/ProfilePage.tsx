import { useState, useEffect } from 'react'
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  Avatar,
  Divider,
  Alert,
} from '@mui/material'
import {
  TrendingUp as TrendingUpIcon,
  School as SchoolIcon,
  Psychology as PsychologyIcon,
  EmojiEvents as EmojiEventsIcon,
  Timer as TimerIcon,
  LocalFireDepartment as FireIcon,
} from '@mui/icons-material'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts'
import axios from 'axios'

// ============================================================================
// ТИПЫ
// ============================================================================

interface UserProfile {
  id: number
  username: string
  total_points: number
  level: string
  completed_lessons: number[]
  completed_cases: number[]
}

interface DailyProgress {
  date: string
  points_earned: number
  modules_completed: number
  cases_solved: number
  lessons_completed: number
  time_spent_minutes: number
}

interface UserStats {
  total_points: number
  total_modules: number
  total_cases: number
  total_lessons: number
  total_time_minutes: number
  current_streak: number
}

interface TopStock {
  ticker: string
  probability: number
  recommendation: string
  current_price: number
}

// ============================================================================
// ДАННЫЕ ДЛЯ ГОРОСКОПА
// ============================================================================

const HOROSCOPES = [
  {
    sign: '🐂 Бык',
    prediction: 'Сегодня отличный день для покупки акций Сбербанка! Звезды говорят о росте на 3%',
    gif: 'https://media.giphy.com/media/MDJ9IbxxvDUQM/giphy.gif',
  },
  {
    sign: '🐻 Медведь',
    prediction: 'Лучше переждать волатильность. Газпром может упасть на 2% сегодня',
    gif: 'https://media.giphy.com/media/BzyTuYCmvFqd1Wqdvw/giphy.gif',
  },
  {
    sign: '🦅 Орёл',
    prediction: 'Время для рискованных инвестиций! Лукойл покажет рост',
    gif: 'https://media.giphy.com/media/11sBLVxNs7v6WA/giphy.gif',
  },
  {
    sign: '🐬 Дельфин',
    prediction: 'Интуиция подскажет верное решение. Прислушайся к внутреннему голосу',
    gif: 'https://media.giphy.com/media/3o7TKSjRrfIPjeiVyM/giphy.gif',
  },
]

const CAT_TIPS = [
  '💡 Терпение — ключ к прибыли. Коты ждут добычу часами!',
  '💡 Диверсификация — как иметь несколько мисок с кормом',
  '💡 Покупай на страхах, продавай на жадности',
  '💡 Не инвестируй больше, чем готов потерять',
  '💡 Изучай компании перед покупкой акций',
  '💡 Долгосрочные инвестиции выгоднее спекуляций',
  '💡 Реинвестируй дивиденды для сложного процента',
  '💡 Следите за ключевой ставкой ЦБ',
]

// ============================================================================
// КОМПОНЕНТ
// ============================================================================

export default function ProfilePage() {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [stats, setStats] = useState<UserStats | null>(null)
  const [progressData, setProgressData] = useState<DailyProgress[]>([])
  const [topStocks, setTopStocks] = useState<TopStock[]>([])
  const [loading, setLoading] = useState(true)
  
  // Случайный гороскоп и совет
  const [horoscope] = useState(() => 
    HOROSCOPES[Math.floor(Math.random() * HOROSCOPES.length)]
  )
  const [catTip] = useState(() => 
    CAT_TIPS[Math.floor(Math.random() * CAT_TIPS.length)]
  )

  // ============================================================================
  // ЗАГРУЗКА ДАННЫХ
  // ============================================================================

  useEffect(() => {
    loadUserData()
  }, [])

  const loadUserData = async () => {
    try {
      // Используем демо-пользователя (id=1)
      const userId = 1

      // Загружаем профиль
      const userResponse = await axios.get(`http://localhost:8000/api/users/${userId}`)
      setUser(userResponse.data)

      // Загружаем статистику
      const statsResponse = await axios.get(`http://localhost:8000/api/users/${userId}/stats`)
      setStats(statsResponse.data)

      // Загружаем прогресс по дням
      const progressResponse = await axios.get(
        `http://localhost:8000/api/users/${userId}/daily-progress?days=30`
      )
      setProgressData(progressResponse.data)

      // Загружаем топ акций
      const stocksResponse = await axios.get('http://localhost:8000/api/ml/top-stocks')
      setTopStocks(stocksResponse.data.top_stocks?.slice(0, 5) || [])

    } catch (error) {
      console.error('Ошибка загрузки данных:', error)
    } finally {
      setLoading(false)
    }
  }

  // ============================================================================
  // РЕНДЕР
  // ============================================================================

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <LinearProgress />
        <Typography align="center" sx={{ mt: 4 }}>
          Загрузка личного кабинета...
        </Typography>
      </Container>
    )
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      
      {/* ================================================================
          ЗАГОЛОВОК
      ================================================================ */}
      <Paper sx={{ p: 3, mb: 3, bgcolor: 'primary.main', color: 'primary.contrastText' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Avatar sx={{ bgcolor: 'background.paper', color: 'primary.main' }}>
            <EmojiEventsIcon fontSize="large" />
          </Avatar>
          <Box>
            <Typography variant="h4" fontWeight="bold">
              Личный кабинет
            </Typography>
            <Typography variant="body1" sx={{ opacity: 0.9 }}>
              {user?.username || 'Пользователь'} • {user?.level || 'Новичок'}
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* ================================================================
          ВЕРХНЯЯ СТАТИСТИКА
      ================================================================ */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        
        {/* Общий балл */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: 'primary.lighter' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <EmojiEventsIcon color="primary" />
                <Typography variant="body2" color="text.secondary">
                  Общий балл
                </Typography>
              </Box>
              <Typography variant="h3" fontWeight="bold" color="primary.main">
                {stats?.total_points || user?.total_points || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Пройдено уроков */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: 'secondary.lighter' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <SchoolIcon color="secondary" />
                <Typography variant="body2" color="text.secondary">
                  Уроков пройдено
                </Typography>
              </Box>
              <Typography variant="h3" fontWeight="bold" color="secondary.main">
                {user?.completed_lessons?.length || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Решено кейсов */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: 'success.lighter' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <PsychologyIcon color="success" />
                <Typography variant="body2" color="text.secondary">
                  Кейсов решено
                </Typography>
              </Box>
              <Typography variant="h3" fontWeight="bold" color="success.main">
                {user?.completed_cases?.length || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Серия дней */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: 'warning.lighter' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <FireIcon color="warning" />
                <Typography variant="body2" color="text.secondary">
                  Дней подряд
                </Typography>
              </Box>
              <Typography variant="h3" fontWeight="bold" color="warning.main">
                {stats?.current_streak || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* ================================================================
          ГРАФИКИ И ГОРОСКОП
      ================================================================ */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        
        {/* График активности */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              📊 Активность по дням
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={progressData}>
                <defs>
                  <linearGradient id="colorPoints" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4fc3f7" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#4fc3f7" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={(date) => new Date(date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })}
                  stroke="#888"
                />
                <YAxis stroke="#888" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1a1d23', 
                    border: '1px solid #333',
                    borderRadius: '8px'
                  }}
                  labelFormatter={(date) => new Date(date).toLocaleDateString('ru-RU')}
                />
                <Area 
                  type="monotone" 
                  dataKey="points_earned" 
                  stroke="#4fc3f7" 
                  fillOpacity={1} 
                  fill="url(#colorPoints)" 
                  name="Очки"
                />
                <Line 
                  type="monotone" 
                  dataKey="time_spent_minutes" 
                  stroke="#81c784" 
                  strokeWidth={2}
                  dot={false}
                  name="Время (мин)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Гороскоп акций */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              🔮 Гороскоп акций
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Box sx={{ textAlign: 'center', mb: 2 }}>
              <Typography variant="h4" mb={1}>
                {horoscope.sign}
              </Typography>
              <Box
                component="img"
                src={horoscope.gif}
                alt="Cat investor"
                sx={{ 
                  width: '100%', 
                  maxHeight: 200, 
                  objectFit: 'cover',
                  borderRadius: 2,
                  mb: 2
                }}
              />
            </Box>
            
            <Alert severity="info" sx={{ mb: 2 }}>
              {horoscope.prediction}
            </Alert>
            
            <Alert severity="success" icon={<TrendingUpIcon />}>
              <Typography variant="body2" fontWeight="bold">
                Совет кота-инвестора:
              </Typography>
              {catTip}
            </Alert>
          </Paper>
        </Grid>
      </Grid>

      {/* ================================================================
          ТОП АКЦИЙ И ДЕТАЛЬНАЯ СТАТИСТИКА
      ================================================================ */}
      <Grid container spacing={3}>
        
        {/* Топ акций по прогнозу AI */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              🤖 Топ акций по прогнозу AI
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            {topStocks.length > 0 ? (
              topStocks.map((stock, index) => (
                <Card 
                  key={stock.ticker}
                  sx={{ 
                    mb: 2, 
                    bgcolor: stock.probability > 0.6 ? 'success.lighter' : 
                             stock.probability < 0.4 ? 'error.lighter' : 'warning.lighter'
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box>
                        <Typography variant="h6" fontWeight="bold">
                          #{index + 1} {stock.ticker}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          ${stock.current_price.toFixed(2)}
                        </Typography>
                      </Box>
                      <Box sx={{ textAlign: 'right' }}>
                        <Chip
                          label={stock.recommendation}
                          color={stock.probability > 0.6 ? 'success' : 
                                 stock.probability < 0.4 ? 'error' : 'warning'}
                          size="small"
                          sx={{ mb: 1 }}
                        />
                        <Typography variant="body2" fontWeight="bold">
                          {(stock.probability * 100).toFixed(1)}%
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              ))
            ) : (
              <Typography color="text.secondary" align="center" py={4}>
                Загрузка прогнозов...
              </Typography>
            )}
          </Paper>
        </Grid>

        {/* Детальная статистика */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              ⏱️ Детальная статистика
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
              <Typography color="text.secondary">
                <TimerIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                Всего времени:
              </Typography>
              <Typography fontWeight="bold">
                {stats?.total_time_minutes ? `${Math.round(stats.total_time_minutes / 60)} ч ${stats.total_time_minutes % 60} мин` : '0 мин'}
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
              <Typography color="text.secondary">
                <SchoolIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                Пройдено модулей:
              </Typography>
              <Typography fontWeight="bold">
                {stats?.total_modules || 0}
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
              <Typography color="text.secondary">
                <PsychologyIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                Решено кейсов:
              </Typography>
              <Typography fontWeight="bold">
                {stats?.total_cases || 0}
              </Typography>
            </Box>
            
            <Divider sx={{ my: 2 }} />
            
            {/* График пройденных уроков по дням */}
            <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
              📚 Уроков пройдено по дням
            </Typography>
            
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={progressData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={(date) => new Date(date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })}
                  stroke="#888"
                />
                <YAxis stroke="#888" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1a1d23', 
                    border: '1px solid #333',
                    borderRadius: '8px'
                  }}
                />
                <Bar dataKey="lessons_completed" fill="#81c784" name="Уроки" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>

    </Container>
  )
}
