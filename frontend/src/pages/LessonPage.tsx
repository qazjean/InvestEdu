import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import CircleIcon from '@mui/icons-material/Circle'

export default function LessonPage() {
  const { moduleId } = useParams<{ moduleId: string }>()
  const navigate = useNavigate()
  const [module, setModule] = useState<any>(null)
  const [lessons, setLessons] = useState<any[]>([])
  const [completedLessons, setCompletedLessons] = useState<number[]>([])

  useEffect(() => {
    // Загрузка пройденных уроков из localStorage
    const savedCompleted = localStorage.getItem('lessons_completed')
    const completed = savedCompleted ? JSON.parse(savedCompleted) : []
    // Преобразуем все ID в числа для корректного сравнения
    setCompletedLessons(completed.map((id: any) => Number(id)))
  
    // Демо-данные модулей
    const modulesData: Record<string, any> = {
      '1': {
        title: 'Основы инвестирования',
        description: 'Что такое акции, облигации, ETF. Базовые понятия и термины',
        icon: '📚',
      },
      '2': {
        title: 'Фундаментальный анализ',
        description: 'Анализ финансовой отчётности, мультипликаторы, оценка компании',
        icon: '📊',
      },
      '3': {
        title: 'Технический анализ',
        description: 'Графики, паттерны, индикаторы, объёмы',
        icon: '📈',
      },
      '4': {
        title: 'Макроэкономика',
        description: 'Ставки ФРС, инфляция, ВВП, влияние на рынки',
        icon: '🌍',
      },
      '5': {
        title: 'Управление портфелем и практическое инвестирование',
        description: 'Сборка портфеля, распределение активов, ребалансировка, управление рисками, долгосрочные стратегии',
        icon: '🧠',
      },
    }

    setModule(modulesData[moduleId || '1'])

    // Демо-уроки для модуля 1
    const module1Lessons = [
      {
        id: 1,
        title: 'Что такое инвестиция?',
        description: 'Инвестиция vs спекуляция, сложный процент, инфляция и риск',
        duration: '20 мин',
        type: 'theory',
      },
      {
        id: 2,
        title: 'Классы активов. Акции',
        description: 'Акции, облигации, ETF, деньги — что куда вкладывать',
        duration: '25 мин',
        type: 'theory',
      },
      {
        id: 3,
        title: 'Облигации и долговые инструменты',
        description: 'Как работают облигации, купоны, доходность, риски',
        duration: '30 мин',
        type: 'theory',
      },
      {
        id: 4,
        title: 'ETF и взаимные фонды',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 5,
        title: 'Дивиденды и пассивный доход',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 6,
        title: 'Риски инвестора. Виды рисков',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 7,
        title: 'Диверсификация портфеля',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 8,
        title: 'Инвестиционные стратегии и налоги',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
    ]

    // Демо-уроки для модуля 2
    const module2Lessons = [
      {
        id: 9,
        title: 'Что такое фундаментальный анализ',
        description: 'Метод оценки компании на основе бизнеса, финансов и перспектив роста',
        duration: '35 мин',
        type: 'theory',
      },
      {
        id: 10,
        title: 'Как работает бизнес компании',
        description: 'Бизнес-модель, источники дохода, конкурентные преимущества',
        duration: '30 мин',
        type: 'theory',
      },
      {
        id: 11,
        title: 'Финансовая отчётность',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 12,
        title: 'Ключевые финансовые показатели',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 13,
        title: 'Оценка стоимости компании',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 14,
        title: 'Конкурентные преимущества',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 15,
        title: 'Рост компании',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 16,
        title: 'Как анализировать компанию',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'practice',
      },
    ]

    // Демо-уроки для модуля 3
    const module3Lessons = [
      {
        id: 17,
        title: 'Что такое технический анализ',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 18,
        title: 'Типы графиков',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 19,
        title: 'Тренды рынка',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 20,
        title: 'Уровни поддержки и сопротивления',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 21,
        title: 'Индикаторы (MA, RSI, MACD)',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 22,
        title: 'Объёмы торгов',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 23,
        title: 'Графические фигуры',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 24,
        title: 'Управление сделками',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 25,
        title: 'Анализ графика реальной акции',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'practice',
      },
    ]

    // Демо-уроки для модуля 4
    const module4Lessons = [
      {
        id: 26,
        title: 'Как экономика влияет на рынки',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 27,
        title: 'Экономический цикл',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 28,
        title: 'Инфляция',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 29,
        title: 'Центральные банки и процентные ставки',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 30,
        title: 'ВВП и экономический рост',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 31,
        title: 'Безработица',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 32,
        title: 'Денежная масса и ликвидность',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 33,
        title: 'Как инвестору использовать макроэкономику',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
    ]

    // Демо-уроки для модуля 5
    const module5Lessons = [
      {
        id: 34,
        title: 'Как собрать инвестиционный портфель',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 35,
        title: 'Asset Allocation (распределение активов)',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 36,
        title: 'Ребалансировка портфеля',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 37,
        title: 'Управление рисками',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 38,
        title: 'Поведенческие ошибки инвесторов',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 39,
        title: 'Долгосрочные стратегии инвестирования',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'theory',
      },
      {
        id: 40,
        title: 'Как построить долгосрочный инвестиционный план',
        description: 'Скоро... Извините, зайдите позже',
        duration: '15 мин',
        type: 'practice',
      },
    ]

    // Выбираем уроки в зависимости от модуля
    if (moduleId === '5') {
      setLessons(module5Lessons)
    } else if (moduleId === '4') {
      setLessons(module4Lessons)
    } else if (moduleId === '3') {
      setLessons(module3Lessons)
    } else if (moduleId === '2') {
      setLessons(module2Lessons)
    } else {
      setLessons(module1Lessons)
    }
  }, [moduleId])

  if (!module) return null

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: { xs: 4, sm: 6 } }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/courses')}
            sx={{ mb: 2 }}
          >
            Назад к курсам
          </Button>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Typography sx={{ fontSize: 48 }}>{module.icon}</Typography>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              {module.title}
            </Typography>
          </Box>
        </Box>

        {/* Lessons List */}
        <Box>
          {lessons.map((lesson, index) => (
            <Card
              key={lesson.id}
              sx={{
                mb: 2,
                transition: 'all 0.2s',
                '&:hover': {
                  bgcolor: 'rgba(255,255,255,0.04)',
                },
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                  <Box
                    sx={{
                      width: 40,
                      height: 40,
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      bgcolor: completedLessons.includes(lesson.id)
                        ? 'success.main'
                        : 'rgba(255,255,255,0.1)',
                    }}
                  >
                    {completedLessons.includes(lesson.id) ? (
                      <CheckCircleIcon sx={{ color: 'background.default' }} />
                    ) : (
                      <Typography sx={{ fontWeight: 600 }}>{index + 1}</Typography>
                    )}
                  </Box>
                  <Box sx={{ flex: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {lesson.title}
                      </Typography>
                      <Chip
                        label={lesson.type === 'theory' ? 'Теория' : lesson.type === 'practice' ? 'Практика' : 'Тест'}
                        size="small"
                        color={lesson.type === 'theory' ? 'primary' : lesson.type === 'practice' ? 'secondary' : 'warning'}
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      {lesson.description}
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: 'right' }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {lesson.duration}
                    </Typography>
                    <Button
                      variant={lesson.description.includes('Скоро') ? 'outlined' : completedLessons.includes(lesson.id) ? 'outlined' : 'contained'}
                      size="small"
                      disabled={lesson.description.includes('Скоро')}
                      onClick={() => navigate(`/courses/${moduleId}/lesson/${lesson.id}`)}
                    >
                      {lesson.description.includes('Скоро') ? 'Скоро...' : completedLessons.includes(lesson.id) ? 'Повторить' : 'Начать'}
                    </Button>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          ))}
        </Box>
      </Box>
    </Container>
  )
}
