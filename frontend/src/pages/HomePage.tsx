import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActionArea,
  Button,
} from '@mui/material'
import { Link } from 'react-router-dom'
import SchoolIcon from '@mui/icons-material/School'
import PsychologyIcon from '@mui/icons-material/Psychology'
import SmartToyIcon from '@mui/icons-material/SmartToy'

const features = [
  {
    icon: <SchoolIcon sx={{ fontSize: 48, color: 'primary.main' }} />,
    title: 'Глубокая теория',
    description: 'Интерактивные уроки от основ до продвинутых стратегий',
    link: '/courses',
  },
  {
    icon: <PsychologyIcon sx={{ fontSize: 48, color: 'secondary.main' }} />,
    title: 'Реальные кейсы',
    description: 'Разбор исторических событий с глубоким анализом',
    link: '/cases',
  },
  {
    icon: <SmartToyIcon sx={{ fontSize: 48, color: 'success.main' }} />,
    title: 'AI Assistant',
    description: 'Прогнозы и анализ реальных акций с помощью ML',
    link: '/ai-assistant',
  },
]

export default function HomePage() {
  return (
    <Container maxWidth="lg">
      <Box sx={{ py: { xs: 4, sm: 8 } }}>
        {/* Hero Section */}
        <Box
          sx={{
            textAlign: 'center',
            mb: 8,
            pt: { xs: 4, sm: 8 },
          }}
        >
          <Typography
            variant="h1"
            sx={{
              fontSize: { xs: '2rem', sm: '3rem', md: '4rem' },
              mb: 2,
              background: 'linear-gradient(135deg, #4fc3f7 0%, #81c784 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Научись инвестировать
          </Typography>
          <Typography
            variant="h5"
            sx={{
              color: 'text.secondary',
              mb: 4,
              maxWidth: '600px',
              mx: 'auto',
            }}
          >
            Глубокое обучение инвестициям через интерактивную теорию, разбор реальных кейсов и AI прогнозы
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
            <Button
              component={Link}
              to="/courses"
              variant="contained"
              size="large"
              sx={{ px: 4 }}
            >
              Начать обучение
            </Button>
            <Button
              component={Link}
              to="/cases"
              variant="outlined"
              size="large"
              sx={{ px: 4 }}
            >
              Смотреть кейсы
            </Button>
          </Box>
        </Box>

        {/* Features */}
        <Grid container spacing={4}>
          {features.map((feature, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <Card
                sx={{
                  height: '100%',
                  transition: 'transform 0.2s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                  },
                }}
              >
                <CardActionArea component={Link} to={feature.link} sx={{ p: 3 }}>
                  <Box sx={{ mb: 2 }}>{feature.icon}</Box>
                  <CardContent sx={{ p: 0 }}>
                    <Typography variant="h6" sx={{ mb: 1 }}>
                      {feature.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {feature.description}
                    </Typography>
                  </CardContent>
                </CardActionArea>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* Stats */}
        <Box
          sx={{
            mt: 8,
            p: 4,
            borderRadius: 2,
            bgcolor: 'background.paper',
            textAlign: 'center',
          }}
        >
          <Typography variant="h4" sx={{ mb: 3 }}>
            Почему InvestEdu?
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={6} sm={3}>
              <Typography variant="h3" color="primary.main" sx={{ fontWeight: 700 }}>
                5
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Модулей обучения
              </Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="h3" color="secondary.main" sx={{ fontWeight: 700 }}>
                40+
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Глубоких кейсов
              </Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="h3" color="success.main" sx={{ fontWeight: 700 }}>
                100%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Практики
              </Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="h3" color="warning.main" sx={{ fontWeight: 700 }}>
                0₽
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Бесплатно
              </Typography>
            </Grid>
          </Grid>
        </Box>
      </Box>
    </Container>
  )
}
