import { useState } from 'react'
import {
  Box,
  Container,
  Typography,
  Paper,
  TextField,
  Button,
  Alert,
  Chip,
  CircularProgress,
  Grid,
  Card,
  CardContent,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText
} from '@mui/material'
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon
} from '@mui/icons-material'
import axios from 'axios'

interface PredictionReport {
  ticker: string
  recommendation: string
  probability: number
  current_price: number
  factors?: {
    positive: string[]
    negative: string[]
    neutral: string[]
  }
}

export default function AIAssistantPage() {
  const [ticker, setTicker] = useState('')
  const [loading, setLoading] = useState(false)
  const [prediction, setPrediction] = useState<PredictionReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [csvFile, setCsvFile] = useState<File | null>(null)

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setCsvFile(event.target.files[0])
    }
  }

  const handlePredict = async () => {
    if (!ticker.trim()) {
      setError('Введите название акции')
      return
    }

    setLoading(true)
    setError(null)
    setPrediction(null)

    try {
      // Создаем FormData для загрузки файла
      const formData = new FormData()
      formData.append('ticker', ticker.toUpperCase())
      
      if (csvFile) {
        formData.append('csv_file', csvFile)
      }

      // Отправляем на backend
      const response = await axios.post(
        'http://localhost:8000/api/ml/predict',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      )

      setPrediction(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка при получении прогноза')
    } finally {
      setLoading(false)
    }
  }

  const getRecommendationColor = (recommendation: string) => {
    if (recommendation.includes('ПОКУПАТЬ')) return 'success'
    if (recommendation.includes('ПРОДАВАТЬ')) return 'error'
    return 'warning'
  }

  const getRecommendationIcon = (recommendation: string) => {
    if (recommendation.includes('ПОКУПАТЬ')) return <TrendingUpIcon color="success" />
    if (recommendation.includes('ПРОДАВАТЬ')) return <TrendingDownIcon color="error" />
    return <InfoIcon color="warning" />
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Заголовок */}
      <Paper sx={{ p: 3, mb: 3, bgcolor: 'primary.main', color: 'primary.contrastText' }}>
        <Typography variant="h4" component="h1" gutterBottom fontWeight="bold">
          🤖 AI Assistant — Прогноз роста акций
        </Typography>
        <Typography variant="body1" sx={{ opacity: 0.9 }}>
          Машинное обучение для анализа российских акций
        </Typography>
      </Paper>

      {/* Предупреждение */}
      <Alert severity="warning" sx={{ mb: 3 }} icon={<WarningIcon />}>
        <Typography variant="body2" fontWeight="bold">
          Важное предупреждение
        </Typography>
        <Typography variant="body2">
          Модель показывает достаточно высокую точность на исторических данных, но не гарантирует 100% результат.
          Это аналитический инструмент, а не инвестиционная рекомендация.
          Всегда проводите собственный анализ перед инвестированием.
        </Typography>
      </Alert>

      {/* Информация о модели */}
      <Paper sx={{ p: 2, mb: 3, bgcolor: 'info.lighter' }}>
        <Typography variant="body2" fontWeight="bold" gutterBottom>
          📊 О модели:
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={6} sm={3}>
            <Chip label="Accuracy: 80%, ROC-AUC: 89%" color="success" size="small" />
          </Grid>
          <Grid item xs={6} sm={3}>
            <Chip label="45 акций MOEX" size="small" />
          </Grid>
          <Grid item xs={6} sm={3}>
            <Chip label="27 признаков" size="small" />
          </Grid>
          <Grid item xs={6} sm={3}>
            <Chip label="168K примеров" size="small" />
          </Grid>
        </Grid>
        <Typography variant="caption" sx={{ mt: 1, display: 'block', color: 'text.secondary' }}>
          Обучена на данных 2024 года. Учитывает параметры макроэкономики: курс доллара, цена на нефть, ключевая ставка и уровень инфляции.
        </Typography>
      </Paper>

      {/* Форма ввода */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          📈 Введите данные для прогноза
        </Typography>
        <Divider sx={{ mb: 2 }} />

        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Тикер акции"
              placeholder="SBER, GAZP, LKOH"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              helperText="Например: SBER для Сбербанка"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <Button
              variant="outlined"
              component="label"
              fullWidth
              sx={{ height: 56 }}
            >
              📁 Загрузить CSV (опционально)
              <input
                type="file"
                accept=".csv"
                hidden
                onChange={handleFileChange}
              />
            </Button>
            {csvFile && (
              <Typography variant="caption" color="success.main" sx={{ mt: 1, display: 'block' }}>
                ✅ Файл: {csvFile.name}
              </Typography>
            )}
          </Grid>

          <Grid item xs={12}>
            <Button
              variant="contained"
              size="large"
              onClick={handlePredict}
              disabled={loading || !ticker.trim()}
              fullWidth
              sx={{ height: 56 }}
            >
              {loading ? <CircularProgress size={24} /> : '🔮 Получить прогноз'}
            </Button>
          </Grid>
        </Grid>

        {/* Инструкция */}
        <Box sx={{ mt: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
          <Typography variant="body2" fontWeight="bold" gutterBottom>
            📚 Как использовать:
          </Typography>
          <Typography variant="body2" component="div">
            <ol style={{ margin: 0, paddingLeft: 20 }}>
              <li>Введите тикер акции (например, SBER)</li>
              <li>Скачайте CSV с данными:
                <ul>
                  <li><a href="https://www.investing.com/equities/sberbank_rts" target="_blank" rel="noopener noreferrer">SBER с Investing.com</a></li>
                  <li><a href="https://www.investing.com/equities/gazprom_rts" target="_blank" rel="noopener noreferrer">GAZP с Investing.com</a></li>
                  <li><a href="https://www.investing.com/equities/lukoil_rts" target="_blank" rel="noopener noreferrer">LKOH с Investing.com</a></li>
                </ul>
              </li>
              <li>Загрузите CSV файл (минимум 200 дней данных)</li>
              <li>Нажмите "Получить прогноз"</li>
            </ol>
          </Typography>
        </Box>
      </Paper>

      {/* Ошибка */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} icon={<ErrorIcon />}>
          {error}
        </Alert>
      )}

      {/* Прогноз */}
      {prediction && (
        <Box>
          {/* Основная карточка */}
          <Card sx={{ mb: 3, bgcolor: `${getRecommendationColor(prediction.recommendation)}.lighter` }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                {getRecommendationIcon(prediction.recommendation)}
                <Typography variant="h5" fontWeight="bold" sx={{ ml: 1 }}>
                  {prediction.recommendation}
                </Typography>
              </Box>

              <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Прогноз (шкала -100 до +100):
                  </Typography>
                  <Typography variant="h4" color={
                    prediction.score > 30 ? 'success.main' : 
                    prediction.score < -30 ? 'error.main' : 'warning.main'
                  } fontWeight="bold">
                    {prediction.score?.toFixed(1)}
                  </Typography>
                  {prediction.score > 50 && (
                    <Typography variant="caption" color="success.main" display="block">
                      🟢 Уверенный рост
                    </Typography>
                  )}
                  {prediction.score > 0 && prediction.score <= 50 && (
                    <Typography variant="caption" color="success.main" display="block">
                      🟢 Скорее рост
                    </Typography>
                  )}
                  {prediction.score === 0 && (
                    <Typography variant="caption" color="warning.main" display="block">
                      🟡 Неопределенность
                    </Typography>
                  )}
                  {prediction.score < 0 && prediction.score >= -50 && (
                    <Typography variant="caption" color="error.main" display="block">
                      🔴 Скорее падение
                    </Typography>
                  )}
                  {prediction.score < -50 && (
                    <Typography variant="caption" color="error.main" display="block">
                      🔴 Уверенное падение
                    </Typography>
                  )}
                </Grid>

                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Текущая цена:
                  </Typography>
                  <Typography variant="h4">
                    ${prediction.current_price.toFixed(2)}
                  </Typography>
                </Grid>

                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Тикер:
                  </Typography>
                  <Typography variant="h4">
                    {prediction.ticker}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Факторы */}
          {prediction.factors && (
            <Grid container spacing={3} sx={{ mt: 2 }}>
              {/* Положительные */}
              {prediction.factors.positive && prediction.factors.positive.length > 0 && (
                <Grid item xs={12} md={4}>
                  <Card sx={{ height: '100%', bgcolor: 'success.lighter', border: 1, borderColor: 'success.main' }}>
                    <CardContent>
                      <Typography variant="h6" color="success.main" gutterBottom fontWeight="bold">
                        <CheckCircleIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
                        Положительные ({prediction.factors.positive.length})
                      </Typography>
                      <Divider sx={{ mb: 2 }} />
                      <List dense>
                        {prediction.factors.positive.map((factor, index) => (
                          <ListItem key={index} sx={{ py: 0.5 }}>
                            <ListItemIcon sx={{ minWidth: 30 }}>
                              <CheckCircleIcon color="success" fontSize="small" />
                            </ListItemIcon>
                            <ListItemText 
                              primary={factor}
                              typography="body2"
                            />
                          </ListItem>
                        ))}
                      </List>
                    </CardContent>
                  </Card>
                </Grid>
              )}

              {/* Нейтральные */}
              {prediction.factors.neutral && prediction.factors.neutral.length > 0 && (
                <Grid item xs={12} md={4}>
                  <Card sx={{ height: '100%', bgcolor: 'warning.lighter', border: 1, borderColor: 'warning.main' }}>
                    <CardContent>
                      <Typography variant="h6" color="warning.main" gutterBottom fontWeight="bold">
                        <InfoIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
                        Нейтральные ({prediction.factors.neutral.length})
                      </Typography>
                      <Divider sx={{ mb: 2 }} />
                      <List dense>
                        {prediction.factors.neutral.map((factor, index) => (
                          <ListItem key={index} sx={{ py: 0.5 }}>
                            <ListItemIcon sx={{ minWidth: 30 }}>
                              <InfoIcon color="warning" fontSize="small" />
                            </ListItemIcon>
                            <ListItemText 
                              primary={factor}
                              typography="body2"
                            />
                          </ListItem>
                        ))}
                      </List>
                    </CardContent>
                  </Card>
                </Grid>
              )}

              {/* Отрицательные */}
              {prediction.factors.negative && prediction.factors.negative.length > 0 && (
                <Grid item xs={12} md={4}>
                  <Card sx={{ height: '100%', bgcolor: 'error.lighter', border: 1, borderColor: 'error.main' }}>
                    <CardContent>
                      <Typography variant="h6" color="error.main" gutterBottom fontWeight="bold">
                        <ErrorIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
                        Отрицательные ({prediction.factors.negative.length})
                      </Typography>
                      <Divider sx={{ mb: 2 }} />
                      <List dense>
                        {prediction.factors.negative.map((factor, index) => (
                          <ListItem key={index} sx={{ py: 0.5 }}>
                            <ListItemIcon sx={{ minWidth: 30 }}>
                              <ErrorIcon color="error" fontSize="small" />
                            </ListItemIcon>
                            <ListItemText 
                              primary={factor}
                              typography="body2"
                            />
                          </ListItem>
                        ))}
                      </List>
                    </CardContent>
                  </Card>
                </Grid>
              )}
            </Grid>
          )}
        </Box>
      )}
    </Container>
  )
}
