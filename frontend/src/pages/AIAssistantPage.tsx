import { useState, useEffect } from 'react'
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
  Error as ErrorIcon,
  CurrencyBitcoin as CurrencyIcon,
  ShowChart as ChartIcon
} from '@mui/icons-material'
import axios from 'axios'

interface MacroData {
  key_rate: number;
  usd_rub: number;
  eur_rub: number;
  oil_price: number;
  inflation: number;
  loaded: boolean;
}

interface PredictionReport {
  ticker: string
  recommendation: string
  probability: number
  current_price: number
  probability_7d?: number
  probability_30d?: number
  score?: number
  factors?: {
    positive: string[]
    negative: string[]
    neutral: string[]
  }
  report_text?: string
}

interface TopStock {
  ticker: string
  name: string
  current_price: number
  change: number
  change_percent: number
}

export default function AIAssistantPage() {
  const [ticker, setTicker] = useState('')
  const [loading, setLoading] = useState(false)
  const [prediction, setPrediction] = useState<PredictionReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [csvFile, setCsvFile] = useState<File | null>(null)
  const [macroData, setMacroData] = useState<MacroData | null>(null)
  const [topStocks, setTopStocks] = useState<TopStock[]>([])
  const [topStocksLoading, setTopStocksLoading] = useState(false)

  useEffect(() => {
    loadMacroData()
    loadTopStocks()
  }, [])

  const loadMacroData = async () => {
    try {
      // Загрузка из backend API (с кэшированием)
      const response = await fetch('http://localhost:8000/api/ml/macro')
      const data = await response.json()

      setMacroData({
        key_rate: data.key_rate || 18.0,
        usd_rub: data.usd_rub || 90.0,
        eur_rub: data.eur_rub || 98.0,
        oil_price: data.oil_price || 85.0,
        inflation: data.inflation || 7.5,
        loaded: true,
      })
    } catch (error) {
      console.error('Ошибка загрузки макро данных:', error)
      // Резервные данные
      setMacroData({
        key_rate: 18.0,
        usd_rub: 90.0,
        eur_rub: 98.0,
        oil_price: 85.0,
        inflation: 7.5,
        loaded: true,
      })
    }
  }

  const loadTopStocks = async () => {
    setTopStocksLoading(true)
    try {
      const response = await fetch('http://localhost:8000/api/ml/top-stocks')
      const data = await response.json()
      if (data.top_stocks) {
        setTopStocks(data.top_stocks)
      }
    } catch (error) {
      console.error('Ошибка загрузки топ акций:', error)
    } finally {
      setTopStocksLoading(false)
    }
  }

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
      const formData = new FormData()
      formData.append('ticker', ticker.toUpperCase())
      
      if (csvFile) {
        formData.append('csv_file', csvFile)
      }

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
          Модель v4.0: XGBoost Multiclass + Triple Barrier Method
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

      {/* Популярные акции с ценами */}
      <Paper sx={{ p: 2, mb: 3, bgcolor: 'background.paper' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" fontWeight="bold">
            📊 Популярные акции РФ
          </Typography>
          <Button
            size="small"
            onClick={loadTopStocks}
            disabled={topStocksLoading}
          >
            🔄 Обновить
          </Button>
        </Box>

        {topStocksLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
            <CircularProgress />
          </Box>
        ) : topStocks.length > 0 ? (
          <Grid container spacing={2}>
            {topStocks.map((stock, index) => (
              <Grid item xs={12} sm={6} md={4} key={stock.ticker}>
                <Card
                  sx={{
                    bgcolor: stock.change > 0 ? 'success.lighter' :
                             stock.change < 0 ? 'error.lighter' : 'grey.100',
                    border: 1,
                    borderColor: stock.change > 0 ? 'success.main' :
                               stock.change < 0 ? 'error.main' : 'grey.300'
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="h6" fontWeight="bold">
                        {stock.ticker}
                      </Typography>
                      <Chip
                        label={stock.change >= 0 ? `+${stock.change_percent.toFixed(2)}%` : `${stock.change_percent.toFixed(2)}%`}
                        color={stock.change >= 0 ? 'success' : 'error'}
                        size="small"
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {stock.name}
                    </Typography>
                    <Divider sx={{ my: 1 }} />
                    <Typography variant="body1" fontWeight="bold">
                      {stock.current_price > 0 ? `${stock.current_price.toFixed(2)} ₽` : 'N/A'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {stock.change >= 0 ? '▲' : '▼'} {stock.change.toFixed(2)} ₽
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        ) : (
          <Typography variant="body2" color="text.secondary">
            Загрузка данных...
          </Typography>
        )}
      </Paper>

      {/* Макро данные */}
      {macroData && (
        <Paper sx={{ p: 2, mb: 3, bgcolor: 'background.paper' }}>
          <Typography variant="body2" fontWeight="bold" gutterBottom>
            📊 Макроэкономика (актуальные данные ЦБ РФ):
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={6} sm={3}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CurrencyIcon color="action" fontSize="small" />
                <Box>
                  <Typography variant="caption" color="text.secondary">Ключевая ставка</Typography>
                  <Typography variant="body1" fontWeight="bold" color={macroData.key_rate > 15 ? 'error' : 'success'}>
                    {macroData.key_rate.toFixed(1)}%
                  </Typography>
                </Box>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <ChartIcon color="action" fontSize="small" />
                <Box>
                  <Typography variant="caption" color="text.secondary">USD/RUB</Typography>
                  <Typography variant="body1" fontWeight="bold">{macroData.usd_rub.toFixed(2)}</Typography>
                </Box>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <ChartIcon color="action" fontSize="small" />
                <Box>
                  <Typography variant="caption" color="text.secondary">EUR/RUB</Typography>
                  <Typography variant="body1" fontWeight="bold">{macroData.eur_rub.toFixed(2)}</Typography>
                </Box>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CurrencyIcon color="action" fontSize="small" />
                <Box>
                  <Typography variant="caption" color="text.secondary">Нефть Brent</Typography>
                  <Typography variant="body1" fontWeight="bold" color={macroData.oil_price > 80 ? 'success' : 'warning'}>
                    ${macroData.oil_price.toFixed(1)}
                  </Typography>
                </Box>
              </Box>
            </Grid>
          </Grid>
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            Источник: ЦБ РФ (cbr-xml-daily.ru) • Обновляется автоматически
          </Typography>
        </Paper>
      )}

      {/* Информация о модели */}
      <Paper sx={{ p: 2, mb: 3, bgcolor: 'info.lighter' }}>
        <Typography variant="body2" fontWeight="bold" gutterBottom>
          📊 О модели v4.0:
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={6} sm={3}>
            <Chip label="Triple Barrier Method" color="primary" size="small" />
          </Grid>
          <Grid item xs={6} sm={3}>
            <Chip label="XGBoost Multiclass" size="small" />
          </Grid>
          <Grid item xs={6} sm={3}>
            <Chip label="27 признаков" size="small" />
          </Grid>
          <Grid item xs={6} sm={3}>
            <Chip label="790K+ примеров" size="small" />
          </Grid>
        </Grid>
        <Typography variant="caption" sx={{ mt: 1, display: 'block', color: 'text.secondary' }}>
          Обучена на данных MOEX 1999-2024. Макро признаки: ключевая ставка, USD/RUB, нефть Brent, инфляция.
          Горизонты: 7 и 30 дней. Метрики: ROC-AUC ~0.61-0.68.
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
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Вероятность роста:
                  </Typography>
                  <Typography variant="h4" color={
                    prediction.probability > 0.6 ? 'success.main' :
                    prediction.probability < 0.4 ? 'error.main' : 'warning.main'
                  } fontWeight="bold">
                    {(prediction.probability * 100).toFixed(1)}%
                  </Typography>
                  {prediction.probability > 0.6 && (
                    <Typography variant="caption" color="success.main" display="block">
                      🟢 Высокая вероятность роста
                    </Typography>
                  )}
                  {prediction.probability > 0.4 && prediction.probability <= 0.6 && (
                    <Typography variant="caption" color="warning.main" display="block">
                      🟡 Неопределенность
                    </Typography>
                  )}
                  {prediction.probability <= 0.4 && (
                    <Typography variant="caption" color="error.main" display="block">
                      🔴 Низкая вероятность роста
                    </Typography>
                  )}
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Текущая цена:
                  </Typography>
                  <Typography variant="h4">
                    ${prediction.current_price.toFixed(2)}
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
