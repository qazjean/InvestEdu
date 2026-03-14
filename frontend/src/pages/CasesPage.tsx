import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  Button,
  CircularProgress,
  LinearProgress,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton
} from '@mui/material'
import { Info as InfoIcon } from '@mui/icons-material'
import axios from 'axios'

interface Case {
  id: number
  title: string
  description: string
  difficulty: string
  category: string
  year: number
  points: number
}

const difficultyColors: Record<string, 'success' | 'warning' | 'error'> = {
  easy: 'success',
  medium: 'warning',
  hard: 'error'
}

const difficultyLabels: Record<string, string> = {
  easy: 'Лёгкий',
  medium: 'Средний',
  hard: 'Сложный'
}

export default function CasesPage() {
  const navigate = useNavigate()
  const [cases, setCases] = useState<Case[]>([])
  const [loading, setLoading] = useState(true)
  
  // Загрузка прогресса из localStorage
  const [completed, setCompleted] = useState<number[]>(() => {
    const saved = localStorage.getItem('cases_completed')
    return saved ? JSON.parse(saved) : []
  })
  const [totalPoints, setTotalPoints] = useState<number>(() => {
    const saved = localStorage.getItem('cases_totalPoints')
    return saved ? parseInt(saved, 10) : 0
  })
  const [infoOpen, setInfoOpen] = useState(false)
  const [selectedDifficulty, setSelectedDifficulty] = useState<string | null>(null)

  // Сохранение прогресса в localStorage при изменении
  useEffect(() => {
    localStorage.setItem('cases_completed', JSON.stringify(completed))
  }, [completed])

  useEffect(() => {
    localStorage.setItem('cases_totalPoints', totalPoints.toString())
  }, [totalPoints])

  // Загрузка кейсов и обновление прогресса
  useEffect(() => {
    axios.get('http://localhost:8000/api/cases/')
      .then(res => {
        setCases(res.data)
        setLoading(false)
        
        // Проверяем, есть ли новые кейсы, и обновляем completed
        const loadedCaseIds = res.data.map((c: Case) => c.id)
        const validCompleted = completed.filter(id => loadedCaseIds.includes(id))
        if (validCompleted.length !== completed.length) {
          setCompleted(validCompleted)
        }
      })
      .catch(err => {
        console.error(err)
        setLoading(false)
      })
  }, [])

  // Обновление прогресса при возврате на страницу (когда localStorage изменился)
  useEffect(() => {
    // Функция обновления из localStorage
    const updateFromLocalStorage = () => {
      const savedCompleted = localStorage.getItem('cases_completed')
      const savedPoints = localStorage.getItem('cases_totalPoints')
      console.log('🔄 Проверка localStorage:', { savedCompleted, savedPoints })
      if (savedCompleted) {
        const parsed = JSON.parse(savedCompleted)
        console.log('   Обновляем completed:', parsed)
        setCompleted(parsed)
      }
      if (savedPoints) {
        const parsed = parseInt(savedPoints, 10)
        console.log('   Обновляем totalPoints:', parsed)
        setTotalPoints(parsed)
      }
    }

    // Проверяем сразу при монтировании (на случай если данные уже есть)
    updateFromLocalStorage()

    // Слушаем изменения storage (работает для разных вкладок)
    window.addEventListener('storage', updateFromLocalStorage)
    // Слушаем фокус (работает при возврате на вкладку)
    window.addEventListener('focus', updateFromLocalStorage)
    // Слушаем visibility change (работает при возврате на вкладку)
    document.addEventListener('visibilitychange', updateFromLocalStorage)
    
    return () => {
      window.removeEventListener('storage', updateFromLocalStorage)
      window.removeEventListener('focus', updateFromLocalStorage)
      document.removeEventListener('visibilitychange', updateFromLocalStorage)
    }
  }, [])

  const handleCaseClick = (caseId: number) => {
    navigate(`/cases/${caseId}`)
  }

  const handleDifficultyFilter = (difficulty: string | null) => {
    setSelectedDifficulty(difficulty)
  }

  const filteredCases = selectedDifficulty
    ? cases.filter(c => c.difficulty === selectedDifficulty)
    : cases

  const progress = cases.length > 0 ? (completed.length / cases.length) * 100 : 0

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Заголовок с прогрессом */}
      <Paper sx={{ p: 3, mb: 3, bgcolor: 'primary.main', color: 'primary.contrastText' }}>
        <Typography variant="h4" component="h1" gutterBottom fontWeight="bold">
          📊 Кейсы для анализа
        </Typography>
        <Typography variant="body1" sx={{ mb: 2, opacity: 0.9 }}>
          Решайте реальные инвестиционные задачи и зарабатывайте баллы
        </Typography>
        
        <Box sx={{ mb: 1, display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="body2">
            Прогресс: {completed.length} из {cases.length}
          </Typography>
          <Typography variant="body2" fontWeight="bold">
            👑 {totalPoints} баллов
          </Typography>
        </Box>
        <LinearProgress 
          variant="determinate" 
          value={progress} 
          sx={{ 
            height: 8, 
            borderRadius: 1,
            bgcolor: 'rgba(255,255,255,0.3)',
            '& .MuiLinearProgress-bar': {
              bgcolor: 'success.main'
            }
          }}
        />
      </Paper>

      {/* Фильтры */}
      <Box sx={{ mb: 3, display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}>
        <Chip 
          label={`Все (${cases.length})`} 
          color={selectedDifficulty === null ? 'primary' : 'default'} 
          variant={selectedDifficulty === null ? 'filled' : 'outlined'}
          onClick={() => handleDifficultyFilter(null)}
          sx={{ cursor: 'pointer' }}
        />
        <Chip 
          label={`Лёгкие (${cases.filter(c => c.difficulty === 'easy').length})`} 
          color={selectedDifficulty === 'easy' ? 'success' : 'default'}
          variant={selectedDifficulty === 'easy' ? 'filled' : 'outlined'}
          onClick={() => handleDifficultyFilter('easy')}
          sx={{ cursor: 'pointer' }}
        />
        <Chip 
          label={`Средние (${cases.filter(c => c.difficulty === 'medium').length})`} 
          color={selectedDifficulty === 'medium' ? 'warning' : 'default'}
          variant={selectedDifficulty === 'medium' ? 'filled' : 'outlined'}
          onClick={() => handleDifficultyFilter('medium')}
          sx={{ cursor: 'pointer' }}
        />
        <Chip 
          label={`Сложные (${cases.filter(c => c.difficulty === 'hard').length})`} 
          color={selectedDifficulty === 'hard' ? 'error' : 'default'}
          variant={selectedDifficulty === 'hard' ? 'filled' : 'outlined'}
          onClick={() => handleDifficultyFilter('hard')}
          sx={{ cursor: 'pointer' }}
        />

        <Button
          startIcon={<InfoIcon />}
          onClick={() => setInfoOpen(true)}
          sx={{ ml: 'auto', textTransform: 'none', fontWeight: 500 }}
          size="small"
          variant="outlined"
        >
          Где искать такие подробные данные в реальной жизни?
        </Button>
      </Box>

      {/* Карточки кейсов */}
      <Grid container spacing={3}>
        {filteredCases.map((caseItem) => (
          <Grid item xs={12} md={6} lg={4} key={caseItem.id}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 6
                },
                position: 'relative',
                ...(completed.includes(caseItem.id) && {
                  opacity: 0.7,
                  bgcolor: 'success.light'
                })
              }}
            >
              {/* Бейдж completed */}
              {completed.includes(caseItem.id) && (
                <Chip
                  label="✅ Решено"
                  size="small"
                  color="success"
                  sx={{
                    position: 'absolute',
                    top: 8,
                    right: 8,
                    zIndex: 1
                  }}
                />
              )}

              <CardContent sx={{ flexGrow: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Chip
                    label={difficultyLabels[caseItem.difficulty] || caseItem.difficulty}
                    color={difficultyColors[caseItem.difficulty] || 'warning'}
                    size="small"
                  />
                  <Chip
                    label={`${caseItem.points} баллов`}
                    size="small"
                    variant="outlined"
                  />
                </Box>

                <Typography variant="h6" gutterBottom>
                  {caseItem.title}
                </Typography>

                <Typography variant="body2" color="text.secondary" paragraph>
                  {caseItem.description}
                </Typography>

                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  <Chip
                    label={caseItem.category}
                    size="small"
                    variant="outlined"
                  />
                  <Chip
                    label={caseItem.year}
                    size="small"
                    variant="outlined"
                  />
                </Box>
              </CardContent>

              <Box sx={{ p: 2, pt: 0 }}>
                <Button
                  variant="contained"
                  fullWidth
                  onClick={() => handleCaseClick(caseItem.id)}
                >
                  {completed.includes(caseItem.id) ? 'Повторить' : 'Начать кейс'}
                </Button>
              </Box>
            </Card>
          </Grid>
        ))}
      </Grid>

      {cases.length === 0 && (
        <Typography textAlign="center" color="text.secondary" sx={{ mt: 4 }}>
          Кейсы загружаются...
        </Typography>
      )}

      {/* Диалог с информацией об источниках данных */}
      <Dialog
        open={infoOpen}
        onClose={() => setInfoOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <InfoIcon color="info" />
          Где инвесторы берут такие данные
        </DialogTitle>
        <DialogContent dividers>
          <Typography variant="body1" paragraph>
            Информация в этом кейсе (финансовые показатели, динамика цены акций, рыночные метрики и события) собрана из публичных источников, которыми пользуются инвесторы и аналитики.
          </Typography>
          
          <Typography variant="body1" paragraph>
            Если вы анализируете реальные компании сегодня, такие данные обычно можно найти в следующих местах.
          </Typography>

          <Typography variant="h6" sx={{ mt: 3, mb: 1 }}>📄 Финансовая отчётность компаний</Typography>
          <Typography variant="body2" paragraph>
            Для американских компаний — квартальные и годовые отчёты (10-Q и 10-K), публикуемые в базе <strong>U.S. Securities and Exchange Commission</strong>.
          </Typography>
          <Typography variant="body2" paragraph>
            Для российских компаний — отчёты по МСФО и РСБУ, публикуемые на сайтах самих компаний, а также в системе раскрытия информации <strong>Интерфакс Центр раскрытия информации</strong> и на сайте <strong>Банк России</strong>.
          </Typography>

          <Typography variant="h6" sx={{ mt: 3, mb: 1 }}>📈 Графики и цены акций</Typography>
          <Typography variant="body2" paragraph>
            Международные платформы для анализа графиков: <strong>TradingView</strong> и <strong>Yahoo Finance</strong>.
          </Typography>
          <Typography variant="body2" paragraph>
            Для российских акций также используются данные биржи <strong>Московская биржа</strong> и аналитические сервисы, работающие с её данными.
          </Typography>

          <Typography variant="h6" sx={{ mt: 3, mb: 1 }}>📊 Финансовые показатели и коэффициенты</Typography>
          <Typography variant="body2" paragraph>
            Для международных компаний — сервисы вроде <strong>Macrotrends</strong> и <strong>Seeking Alpha</strong>.
          </Typography>
          <Typography variant="body2" paragraph>
            Для российских компаний — аналитические платформы и агрегаторы данных, такие как <strong>Smart-Lab</strong> или <strong>Investing.com</strong>.
          </Typography>

          <Typography variant="h6" sx={{ mt: 3, mb: 1 }}>📉 Рыночная статистика</Typography>
          <Typography variant="body2" sx={{ mb: 1 }}>(Short interest, структура владения, объёмы торгов и другие показатели)</Typography>
          <Typography variant="body2" paragraph>
            Для американского рынка — данные на <strong>Nasdaq</strong> и <strong>Yahoo Finance</strong>.
          </Typography>
          <Typography variant="body2" paragraph>
            Для российского рынка — статистика торгов и рыночные данные на сайте <strong>Московская биржа</strong>.
          </Typography>

          <Typography variant="h6" sx={{ mt: 3, mb: 1 }}>📰 Новости и ключевые события компаний</Typography>
          <Typography variant="body2" paragraph>
            Международные деловые СМИ: <strong>Bloomberg</strong> и <strong>Reuters</strong>.
          </Typography>
          <Typography variant="body2" paragraph>
            Для российских компаний — деловые издания и агентства, например <strong>РБК</strong> и <strong>Интерфакс</strong>.
          </Typography>

          <Box sx={{ mt: 3, p: 2, bgcolor: 'info.lighter', borderRadius: 1 }}>
            <Typography variant="body2" fontStyle="italic">
              💡 Профессиональные инвесторы обычно используют несколько источников одновременно, чтобы получить полную картину бизнеса, его финансового состояния и рыночной ситуации.
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInfoOpen(false)} variant="contained">
            Понятно
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  )
}
