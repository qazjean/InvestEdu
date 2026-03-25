import { useState, useEffect } from 'react'
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  LinearProgress,
} from '@mui/material'
import { useNavigate } from 'react-router-dom'

const modules = [
  {
    id: 1,
    title: 'Основы инвестирования',
    description: 'Что такое акции, облигации, ETF. Базовые понятия и термины',
    icon: '📚',
    lessonsCount: 8,
    color: 'primary',
  },
  {
    id: 2,
    title: 'Фундаментальный анализ',
    description: 'Анализ финансовой отчётности, мультипликаторы, оценка компании',
    icon: '📊',
    lessonsCount: 8,
    color: 'secondary',
  },
  {
    id: 3,
    title: 'Технический анализ',
    description: 'Графики, паттерны, индикаторы, объёмы',
    icon: '📈',
    lessonsCount: 9,
    color: 'success',
  },
  {
    id: 4,
    title: 'Макроэкономика',
    description: 'Ставки ФРС, инфляция, ВВП, влияние на рынки',
    icon: '🌍',
    lessonsCount: 8,
    color: 'warning',
  },
  {
    id: 5,
    title: 'Управление портфелем и практическое инвестирование',
    description: 'Сборка портфеля, распределение активов, ребалансировка, управление рисками, долгосрочные стратегии',
    icon: '🧠',
    lessonsCount: 7,
    color: 'error',
  },
]

export default function CoursesPage() {
  const navigate = useNavigate()
  const [progress, setProgress] = useState<Record<number, number>>({})
  const [completedLessons, setCompletedLessons] = useState<number[]>([])

  useEffect(() => {
    // Загрузка прогресса из localStorage
    const savedCompleted = localStorage.getItem('lessons_completed')
    const completed = savedCompleted ? JSON.parse(savedCompleted) : []
    // Преобразуем все ID в числа для корректного сравнения
    setCompletedLessons(completed.map((id: any) => Number(id)))
    
    // Рассчитываем прогресс по модулям
    const modulesLessons: Record<number, number> = {
      1: 8,
      2: 8,
      3: 9,
      4: 8,
      5: 7,
    }
    
    const newProgress: Record<number, number> = {}
    Object.entries(modulesLessons).forEach(([moduleId, lessonsCount]) => {
      const completedInModule = completed.filter(id => {
        // Предполагаем что ID уроков идут по порядку: модуль 1 = 1-8, модуль 2 = 9-16 и тд
        const startId = (parseInt(moduleId) - 1) * 8 + 1
        const endId = startId + lessonsCount - 1
        return id >= startId && id <= endId
      }).length
      newProgress[parseInt(moduleId)] = Math.round((completedInModule / lessonsCount) * 100)
    })
    
    setProgress(newProgress)
  }, [])

  // Обработчик обновления прогресса из LessonViewPage
  useEffect(() => {
    const handleProgressUpdate = (event: CustomEvent) => {
      const { moduleId } = event.detail
      // Пересчитываем прогресс
      const savedCompleted = localStorage.getItem('lessons_completed')
      const completed = savedCompleted ? JSON.parse(savedCompleted) : []
      // Преобразуем все ID в числа
      setCompletedLessons(completed.map((id: any) => Number(id)))
      
      const modulesLessons: Record<number, number> = {
        1: 8,
        2: 8,
        3: 9,
        4: 8,
        5: 7,
      }

      const newProgress: Record<number, number> = {}
      Object.entries(modulesLessons).forEach(([modId, lessonsCount]) => {
        const completedInModule = completed.filter(id => {
          const startId = (parseInt(modId) - 1) * 8 + 1
          const endId = startId + lessonsCount - 1
          return Number(id) >= startId && Number(id) <= endId
        }).length
        newProgress[parseInt(modId)] = Math.round((completedInModule / lessonsCount) * 100)
      })

      setProgress(newProgress)
    }

    window.addEventListener('lessonProgressUpdate' as any, handleProgressUpdate as any)
    return () => window.removeEventListener('lessonProgressUpdate' as any, handleProgressUpdate as any)
  }, [])

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: { xs: 4, sm: 6 } }}>
        <Typography variant="h4" sx={{ mb: 1, fontWeight: 700 }}>
          Курсы обучения
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          Выберите модуль для начала обучения
        </Typography>

        <Grid container spacing={3}>
          {modules.map((module) => (
            <Grid item xs={12} sm={6} md={4} key={module.id}>
              <Card
                onClick={() => navigate(`/courses/${module.id}`)}
                sx={{
                  height: '100%',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: '0 8px 24px rgba(0,0,0,0.3)',
                  },
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ fontSize: 48, mb: 2 }}>{module.icon}</Box>
                  <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>
                    {module.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {module.description}
                  </Typography>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Chip
                      label={`${module.lessonsCount} уроков`}
                      size="small"
                      color={module.color as any}
                      variant="outlined"
                    />
                    <Typography variant="caption" color="text.secondary">
                      {progress[module.id] || 0}% завершено
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={progress[module.id] || 0}
                    sx={{
                      height: 6,
                      borderRadius: 3,
                      bgcolor: 'rgba(255,255,255,0.1)',
                      '& .MuiLinearProgress-bar': {
                        borderRadius: 3,
                        bgcolor: progress[module.id] === 100 ? 'success.main' : progress[module.id]! >= 50 ? 'warning.main' : 'primary.main',
                      },
                    }}
                  />
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>
    </Container>
  )
}
