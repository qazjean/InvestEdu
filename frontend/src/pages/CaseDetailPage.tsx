import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box,
  Container,
  Typography,
  Paper,
  Button,
  Radio,
  RadioGroup,
  FormControlLabel,
  TextField,
  Alert,
  Chip,
  Grid,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  TableHead,
  Divider
} from '@mui/material'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import axios from 'axios'

// Простой парсер Markdown -> React компоненты
function renderMarkdown(text: string) {
  if (!text) return null
  
  const lines = text.split('\n')
  const elements: JSX.Element[] = []
  let listItems: string[] = []
  let inList = false

  const flushList = () => {
    if (listItems.length > 0) {
      elements.push(
        <Box key={`list-${elements.length}`} component="ul" sx={{ mt: 1, mb: 1, pl: 2 }}>
          {listItems.map((item, i) => (
            <li key={i} style={{ marginBottom: '4px' }}>{item}</li>
          ))}
        </Box>
      )
      listItems = []
      inList = false
    }
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]

    // Пустая строка
    if (line.trim() === '') {
      flushList()
      elements.push(<Box key={i} sx={{ height: '8px' }} />)
      continue
    }

    // Заголовок ##
    if (line.startsWith('## ')) {
      flushList()
      elements.push(
        <Typography key={i} variant="h6" sx={{ mt: 2, mb: 1, fontWeight: 'bold' }}>
          {parseInline(line.slice(3))}
        </Typography>
      )
      continue
    }

    // Заголовок #
    if (line.startsWith('# ')) {
      flushList()
      elements.push(
        <Typography key={i} variant="h5" sx={{ mt: 2, mb: 1, fontWeight: 'bold' }}>
          {parseInline(line.slice(2))}
        </Typography>
      )
      continue
    }

    // Список (1. или -)
    const listMatch = line.match(/^(\d+\.|\-)\s*(.*)/)
    if (listMatch) {
      inList = true
      listItems.push(parseInline(listMatch[2]))
      continue
    }

    // Обычный текст
    flushList()
    elements.push(
      <Typography key={i} variant="body1" sx={{ mb: 0.5 }}>
        {parseInline(line)}
      </Typography>
    )
  }

  flushList()
  return <>{elements}</>
}

// Парсер инлайн элементов (**bold**)
function parseInline(text: string) {
  const parts = text.split(/(\*\*.*?\*\*)/g)
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i}>{part.slice(2, -2)}</strong>
    }
    return part
  })
}

// Парсер текста - только заголовки и обычный текст (таблицы отдельно)
function parseContent(text: string) {
  if (!text) return []
  
  const lines = text.split('\n')
  const sections: any[] = []
  let currentText: string[] = []

  const flushText = () => {
    if (currentText.length > 0) {
      const joined = currentText.join('\n').trim()
      if (joined) {
        sections.push({ type: 'text', content: joined })
      }
      currentText = []
    }
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()
    
    // Пустая строка - разделитель
    if (line === '') {
      flushText()
      continue
    }

    // Пропускаем строки с таблицами (содержат |)
    if (line.includes('|')) {
      continue
    }

    // Заголовок раздела (короткая строка без : и |)
    if (line.length < 40 && !line.includes(':') && (i === 0 || lines[i-1]?.trim() === '')) {
      flushText()
      sections.push({ type: 'heading', content: line })
      continue
    }

    // Обычный текст
    currentText.push(line)
  }

  flushText()
  return sections
}

export default function CaseDetailPage() {
  const { caseId } = useParams<{ caseId: string }>()
  const navigate = useNavigate()
  const [caseData, setCaseData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedDecision, setSelectedDecision] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [result, setResult] = useState<any>(null)

  useEffect(() => {
    axios.get(`http://localhost:8000/api/cases/${caseId}`)
      .then(res => { setCaseData(res.data); setLoading(false) })
      .catch(err => { setError(err.message); setLoading(false) })
  }, [caseId])

  const handleSubmit = () => {
    axios.post(`http://localhost:8000/api/cases/${caseId}/submit`, { decision: selectedDecision })
      .then(res => {
        console.log('📤 Отправка результата кейса:', res.data)
        setResult(res.data)
        setSubmitted(true)

        // Обновляем прогресс в localStorage
        if (res.data.is_correct) {
          const caseIdNum = parseInt(caseId || '0', 10)
          const points = res.data.points_earned || 0
          
          // Получаем текущий прогресс
          const savedCompleted = localStorage.getItem('cases_completed')
          const completed: number[] = savedCompleted ? JSON.parse(savedCompleted) : []
          const savedPoints = localStorage.getItem('cases_totalPoints')
          const totalPoints = savedPoints ? parseInt(savedPoints, 10) : 0
          
          // Добавляем кейс если ещё не решён
          if (!completed.includes(caseIdNum)) {
            completed.push(caseIdNum)
            localStorage.setItem('cases_completed', JSON.stringify(completed))
            localStorage.setItem('cases_totalPoints', (totalPoints + points).toString())
            console.log('💾 Прогресс сохранён:', { completed, totalPoints: totalPoints + points })
          }
        }
      })
      .catch(() => setError('Ошибка'))
  }

  const preparePriceData = () => {
    if (caseData?.scenario_data?.price_history) {
      return caseData.scenario_data.price_history.filter((item: any) => item.date && item.price).map((item: any) => ({ date: item.date, price: item.price }))
    }
    return []
  }

  const renderContent = () => {
    const sections = parseContent(caseData.scenario_data?.full_description || '')
    return sections.map((section, idx) => {
      if (section.type === 'heading') {
        return <Typography key={idx} variant="h6" sx={{ mt: 2, mb: 1, color: 'primary.main', fontWeight: 'bold' }}>{section.content}</Typography>
      }
      if (section.type === 'table') {
        return (
          <TableContainer key={idx} sx={{ mb: 2, border: '1px solid #e0e0e0', borderRadius: 1 }}>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: 'primary.light' }}>
                  {section.headers.map((h: string, i: number) => (
                    <TableCell key={i} align={i === 0 ? 'left' : 'right'}>
                      <strong>{h}</strong>
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {section.rows.map((row: string[], i: number) => (
                  <TableRow key={i} sx={{ bgcolor: i % 2 === 1 ? 'action.hover' : 'inherit' }}>
                    {row.map((cell: string, j: number) => (
                      <TableCell key={j} align={j === 0 ? 'left' : 'right'}>{cell}</TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )
      }
      return <Typography key={idx} variant="body1" sx={{ mb: 1, whiteSpace: 'pre-wrap' }}>{section.content}</Typography>
    })
  }

  if (loading) {
    return <Container sx={{ mt: 8, textAlign: 'center' }}><CircularProgress /><Typography sx={{ mt: 2 }}>Загрузка...</Typography></Container>
  }

  if (error) {
    return <Container sx={{ mt: 8 }}><Alert severity="error">{error}</Alert><Button onClick={() => navigate('/cases')}>Назад</Button></Container>
  }

  if (!caseData) {
    return <Container sx={{ mt: 8 }}><Alert severity="warning">Кейс не найден</Alert></Container>
  }

  const priceData = preparePriceData()
  const ticker = caseData.scenario_data?.ticker || 'TSLA'
  const decisionOptions = caseData.task?.decision_options || [
    { id: 'buy', label: 'Купить', description: `Вложить $100,000 в ${ticker}` },
    { id: 'hold', label: 'Держать', description: 'Не действовать' },
    { id: 'sell', label: 'Продать', description: `Избегать ${ticker}` }
  ]

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Button onClick={() => navigate('/cases')} sx={{ mb: 2 }}>← Назад</Button>

      {/* Заголовок */}
      <Paper sx={{ p: 3, mb: 3, bgcolor: 'primary.main', color: 'primary.contrastText' }}>
        <Typography variant="h4" fontWeight="bold">{caseData.title}</Typography>
        <Box sx={{ display: 'flex', gap: 1, mt: 2, flexWrap: 'wrap' }}>
          <Chip label={caseData.difficulty} color={caseData.difficulty === 'hard' ? 'error' : caseData.difficulty === 'medium' ? 'warning' : 'success'} />
          <Chip label={`${caseData.points} баллов`} />
          <Chip label={caseData.year} />
        </Box>
      </Paper>

      {/* Вводная информация */}
      <Paper sx={{ p: 3, mb: 3, bgcolor: 'info.lighter' }}>
        <Typography variant="h6" gutterBottom fontWeight="bold">
          💼 Ваша ситуация
        </Typography>
        <Divider sx={{ mb: 2 }} />
        <Typography variant="body1" paragraph>
          У вас есть <strong>$100,000 наличными</strong> и <strong>100 акций</strong> этой компании,
          купленных ранее.
        </Typography>
        <Typography variant="body1" paragraph>
          Вам нужно выбрать одно из трёх решений:
        </Typography>
        <Box component="ul" sx={{ mt: 1, mb: 1, pl: 2 }}>
          <Typography component="li" variant="body1">
            <strong>Купить</strong> — докупить ещё акций на сумму $100,000
          </Typography>
          <Typography component="li" variant="body1">
            <strong>Держать</strong> — оставить имеющиеся 100 акций без изменений
          </Typography>
          <Typography component="li" variant="body1">
            <strong>Продать</strong> — продать все 100 акций
          </Typography>
        </Box>
      </Paper>

      {/* Описание с таблицами — только если есть контент */}
      {caseData.scenario_data?.full_description && caseData.scenario_data.full_description.trim() !== '' && (
        <Paper sx={{ p: 3, mb: 3 }}>
          {renderContent()}
        </Paper>
      )}

      {/* График цены */}
      {priceData.length > 0 && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>📈 Динамика цены акций</Typography>
          <Divider sx={{ mb: 2 }} />
          <Box sx={{ height: 300 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={priceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="price" stroke="#1976d2" strokeWidth={2} name="Цена ($)" />
              </LineChart>
            </ResponsiveContainer>
          </Box>
        </Paper>
      )}

      <Grid container spacing={3}>
        {/* Левая колонка */}
        <Grid item xs={12} md={6}>
          {/* Финансовые показатели */}
          {caseData.scenario_data?.financials && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>💰 Финансовые показатели</Typography>
              <Divider sx={{ mb: 2 }} />
              <TableContainer>
                <Table size="small">
                  <TableBody>
                    {Object.entries(caseData.scenario_data.financials).map(([key, value]) => (
                      <TableRow key={key}>
                        <TableCell sx={{ fontWeight: 500 }}>{key}</TableCell>
                        <TableCell align="right"><strong>{String(value)}</strong></TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}

          {/* Красные флаги */}
          {caseData.scenario_data?.red_flags && (
            <Paper sx={{ p: 3, mb: 3, border: 2, borderColor: 'error.main' }}>
              <Typography variant="h6" gutterBottom color="error.main" fontWeight="bold">🚩 Красные флаги</Typography>
              <Divider sx={{ mb: 2 }} />
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'error.light', color: 'error.contrastText' }}>
                      {caseData.scenario_data.red_flags.headers.map((h: string, i: number) => (
                        <TableCell key={i} align={i === 0 ? 'left' : 'right'} sx={{ color: 'error.contrastText', fontWeight: 'bold' }}>
                          {h}
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {caseData.scenario_data.red_flags.rows.map((row: string[], i: number) => (
                      <TableRow key={i} sx={{ bgcolor: i % 2 === 1 ? 'action.hover' : 'inherit' }}>
                        {row.map((cell: string, j: number) => (
                          <TableCell key={j} align={j === 0 ? 'left' : 'right'}>{cell}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}

          {/* Санкционные данные */}
          {caseData.scenario_data?.sanctions_data && (
            <Paper sx={{ p: 3, mb: 3, border: 2, borderColor: 'error.main' }}>
              <Typography variant="h6" gutterBottom color="error.main" fontWeight="bold">⚠️ Санкции</Typography>
              <Divider sx={{ mb: 2 }} />
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'error.light', color: 'error.contrastText' }}>
                      {caseData.scenario_data.sanctions_data.headers.map((h: string, i: number) => (
                        <TableCell key={i} align={i === 0 ? 'left' : 'right'} sx={{ color: 'error.contrastText', fontWeight: 'bold' }}>
                          {h}
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {caseData.scenario_data.sanctions_data.rows.map((row: string[], i: number) => (
                      <TableRow key={i} sx={{ bgcolor: i % 2 === 1 ? 'action.hover' : 'inherit' }}>
                        {row.map((cell: string, j: number) => (
                          <TableCell key={j} align={j === 0 ? 'left' : 'right'}>{cell}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}

          {/* Subprime exposure */}
          {caseData.scenario_data?.subprime_exposure && (
            <Paper sx={{ p: 3, mb: 3, border: 2, borderColor: 'error.main' }}>
              <Typography variant="h6" gutterBottom color="error.main" fontWeight="bold">🏠 Subprime Exposure</Typography>
              <Divider sx={{ mb: 2 }} />
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'error.light', color: 'error.contrastText' }}>
                      {caseData.scenario_data.subprime_exposure.headers.map((h: string, i: number) => (
                        <TableCell key={i} align={i === 0 ? 'left' : 'right'} sx={{ color: 'error.contrastText', fontWeight: 'bold' }}>
                          {h}
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {caseData.scenario_data.subprime_exposure.rows.map((row: string[], i: number) => (
                      <TableRow key={i} sx={{ bgcolor: i % 2 === 1 ? 'action.hover' : 'inherit' }}>
                        {row.map((cell: string, j: number) => (
                          <TableCell key={j} align={j === 0 ? 'left' : 'right'}>{cell}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}

          {/* Примеры компаний доткомов */}
          {caseData.scenario_data?.dotcom_examples && (
            <Paper sx={{ p: 3, mb: 3, border: 2, borderColor: 'warning.main' }}>
              <Typography variant="h6" gutterBottom color="warning.main" fontWeight="bold">🌐 Примеры компаний доткомов</Typography>
              <Divider sx={{ mb: 2 }} />
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'warning.light', color: 'warning.contrastText' }}>
                      {caseData.scenario_data.dotcom_examples.headers.map((h: string, i: number) => (
                        <TableCell key={i} align={i === 0 ? 'left' : 'right'} sx={{ color: 'warning.contrastText', fontWeight: 'bold' }}>
                          {h}
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {caseData.scenario_data.dotcom_examples.rows.map((row: string[], i: number) => (
                      <TableRow key={i} sx={{ bgcolor: i % 2 === 1 ? 'action.hover' : 'inherit' }}>
                        {row.map((cell: string, j: number) => (
                          <TableCell key={j} align={j === 0 ? 'left' : 'right'}>{cell}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}

          {/* Риски */}
          {caseData.scenario_data?.risks && (
            <Paper sx={{ p: 3, mb: 3, border: 1, borderColor: 'warning.main' }}>
              <Typography variant="h6" gutterBottom color="warning.main" fontWeight="bold">⚠️ Риски</Typography>
              <Divider sx={{ mb: 2 }} />
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'warning.light', color: 'warning.contrastText' }}>
                      {caseData.scenario_data.risks.headers.map((h: string, i: number) => (
                        <TableCell key={i} align={i === 0 ? 'left' : 'right'} sx={{ color: 'warning.contrastText', fontWeight: 'bold' }}>
                          {h}
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {caseData.scenario_data.risks.rows.map((row: string[], i: number) => (
                      <TableRow key={i} sx={{ bgcolor: i % 2 === 1 ? 'action.hover' : 'inherit' }}>
                        {row.map((cell: string, j: number) => (
                          <TableCell key={j} align={j === 0 ? 'left' : 'right'}>{cell}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}

          {/* Cash Runway */}
          {caseData.scenario_data?.cash_runway && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>💵 Cash Runway</Typography>
              <Divider sx={{ mb: 2 }} />
              <Alert severity="warning" sx={{ mb: 2 }}>
                <strong>Денег осталось:</strong> {caseData.scenario_data.cash_runway.quarters_left} квартала(ов)
              </Alert>
              <Typography variant="body2">{caseData.scenario_data.cash_runway.calculation}</Typography>
              <Typography variant="body2">Ожидаемое окончание: {caseData.scenario_data.cash_runway.end_date}</Typography>
            </Paper>
          )}

          {/* Short Interest данные */}
          {caseData.scenario_data?.short_interest_data && (
            <Paper sx={{ p: 3, mb: 3, border: 2, borderColor: 'warning.main' }}>
              <Typography variant="h6" gutterBottom color="warning.main" fontWeight="bold">📉 Short Interest</Typography>
              <Divider sx={{ mb: 2 }} />
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'warning.light', color: 'warning.contrastText' }}>
                      {caseData.scenario_data.short_interest_data.headers.map((h: string, i: number) => (
                        <TableCell key={i} align={i === 0 ? 'left' : 'right'} sx={{ color: 'warning.contrastText', fontWeight: 'bold' }}>
                          {h}
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {caseData.scenario_data.short_interest_data.rows.map((row: string[], i: number) => (
                      <TableRow key={i} sx={{ bgcolor: i % 2 === 1 ? 'action.hover' : 'inherit' }}>
                        {row.map((cell: string, j: number) => (
                          <TableCell key={j} align={j === 0 ? 'left' : 'right'}>{cell}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}

          {/* Динамика выручки */}
          {caseData.scenario_data?.revenue_trend && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>📈 Динамика выручки</Typography>
              <Divider sx={{ mb: 2 }} />
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'primary.light' }}>
                      {caseData.scenario_data.revenue_trend.headers.map((h: string, i: number) => (
                        <TableCell key={i} align={i === 0 ? 'left' : 'right'}><strong>{h}</strong></TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {caseData.scenario_data.revenue_trend.rows.map((row: string[], i: number) => (
                      <TableRow key={i} sx={{ bgcolor: i % 2 === 1 ? 'action.hover' : 'inherit' }}>
                        {row.map((cell: string, j: number) => (
                          <TableCell key={j} align={j === 0 ? 'left' : 'right'}>{cell}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}

          {/* О компании */}
          {caseData.scenario_data?.company_facts && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>🏢 О компании</Typography>
              <Divider sx={{ mb: 2 }} />
              {caseData.scenario_data.company_facts.map((fact: string, i: number) => (
                <Typography key={i} variant="body2" sx={{ py: 0.5 }}>{fact}</Typography>
              ))}
            </Paper>
          )}

          {/* Индикаторы пузыря */}
          {caseData.scenario_data?.bubble_indicators && (
            <Paper sx={{ p: 3, mb: 3, border: 1, borderColor: 'error.main' }}>
              <Typography variant="h6" gutterBottom color="error.main" fontWeight="bold">🚩 Индикаторы пузыря</Typography>
              <Divider sx={{ mb: 2 }} />
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'error.light', color: 'error.contrastText' }}>
                      {caseData.scenario_data.bubble_indicators.headers.map((h: string, i: number) => (
                        <TableCell key={i} align={i === 0 ? 'left' : 'right'} sx={{ color: 'error.contrastText', fontWeight: 'bold' }}>
                          {h}
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {caseData.scenario_data.bubble_indicators.rows.map((row: string[], i: number) => (
                      <TableRow key={i} sx={{ bgcolor: i % 2 === 1 ? 'action.hover' : 'inherit' }}>
                        {row.map((cell: string, j: number) => (
                          <TableCell key={j} align={j === 0 ? 'left' : 'right'}>{cell}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}
        </Grid>

        {/* Правая колонка */}
        <Grid item xs={12} md={6}>
          {/* Сравнение с конкурентами */}
          {caseData.scenario_data?.comparison && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>🏆 Сравнение с конкурентами</Typography>
              <Divider sx={{ mb: 2 }} />
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'primary.light' }}>
                      {caseData.scenario_data.comparison.headers.map((h: string, i: number) => (
                        <TableCell key={i} align={i === 0 ? 'left' : 'right'}><strong>{h}</strong></TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {caseData.scenario_data.comparison.rows.map((row: string[], i: number) => (
                      <TableRow key={i} sx={{ bgcolor: i % 2 === 1 ? 'action.hover' : 'inherit' }}>
                        {row.map((cell: string, j: number) => (
                          <TableCell key={j} align={j === 0 ? 'left' : 'right'}>{cell}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}

          {/* Model 3 Производство */}
          {caseData.scenario_data?.production && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>🚙 Model 3: Производство</Typography>
              <Divider sx={{ mb: 2 }} />
              <Typography variant="body2" gutterBottom><strong>Цель:</strong> {caseData.scenario_data.production.target}</Typography>
              <Typography variant="body2" gutterBottom><strong>Текущий:</strong> {caseData.scenario_data.production.current}</Typography>
              <TableContainer sx={{ mt: 2 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'primary.light' }}>
                      {caseData.scenario_data.production.headers.map((h: string, i: number) => (
                        <TableCell key={i} align={i === 0 ? 'left' : 'right'}><strong>{h}</strong></TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {caseData.scenario_data.production.rows.map((row: string[], i: number) => (
                      <TableRow key={i} sx={{ bgcolor: i % 2 === 1 ? 'action.hover' : 'inherit' }}>
                        {row.map((cell: string, j: number) => (
                          <TableCell key={j} align={j === 0 ? 'left' : 'right'}>{cell}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}

          {/* Сравнение с кризисами */}
          {caseData.scenario_data?.crisis_comparison && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>📉 Сравнение с кризисами</Typography>
              <Divider sx={{ mb: 2 }} />
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'primary.light' }}>
                      {caseData.scenario_data.crisis_comparison.headers.map((h: string, i: number) => (
                        <TableCell key={i} align={i === 0 ? 'left' : 'right'}><strong>{h}</strong></TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {caseData.scenario_data.crisis_comparison.rows.map((row: string[], i: number) => (
                      <TableRow key={i} sx={{ bgcolor: i % 2 === 1 ? 'action.hover' : 'inherit' }}>
                        {row.map((cell: string, j: number) => (
                          <TableCell key={j} align={j === 0 ? 'left' : 'right'}>{cell}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}

          {/* Сравнение с другими банками */}
          {caseData.scenario_data?.bank_comparison && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>🏦 Сравнение с банками</Typography>
              <Divider sx={{ mb: 2 }} />
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'primary.light' }}>
                      {caseData.scenario_data.bank_comparison.headers.map((h: string, i: number) => (
                        <TableCell key={i} align={i === 0 ? 'left' : 'right'}><strong>{h}</strong></TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {caseData.scenario_data.bank_comparison.rows.map((row: string[], i: number) => (
                      <TableRow key={i} sx={{ bgcolor: i % 2 === 1 ? 'action.hover' : 'inherit' }}>
                        {row.map((cell: string, j: number) => (
                          <TableCell key={j} align={j === 0 ? 'left' : 'right'}>{cell}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}

          {/* Динамика левериджа */}
          {caseData.scenario_data?.leverage_trend && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>📊 Динамика левериджа</Typography>
              <Divider sx={{ mb: 2 }} />
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'primary.light' }}>
                      {caseData.scenario_data.leverage_trend.headers.map((h: string, i: number) => (
                        <TableCell key={i} align={i === 0 ? 'left' : 'right'}><strong>{h}</strong></TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {caseData.scenario_data.leverage_trend.rows.map((row: string[], i: number) => (
                      <TableRow key={i} sx={{ bgcolor: i % 2 === 1 ? 'action.hover' : 'inherit' }}>
                        {row.map((cell: string, j: number) => (
                          <TableCell key={j} align={j === 0 ? 'left' : 'right'}>{cell}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}

          {/* Кризис ликвидности */}
          {caseData.scenario_data?.liquidity_crisis && (
            <Paper sx={{ p: 3, mb: 3, border: 1, borderColor: 'error.main' }}>
              <Typography variant="h6" gutterBottom color="error.main" fontWeight="bold">💧 Кризис ликвидности</Typography>
              <Divider sx={{ mb: 2 }} />
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'error.light', color: 'error.contrastText' }}>
                      {caseData.scenario_data.liquidity_crisis.headers.map((h: string, i: number) => (
                        <TableCell key={i} align={i === 0 ? 'left' : 'right'} sx={{ color: 'error.contrastText', fontWeight: 'bold' }}>
                          {h}
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {caseData.scenario_data.liquidity_crisis.rows.map((row: string[], i: number) => (
                      <TableRow key={i} sx={{ bgcolor: i % 2 === 1 ? 'action.hover' : 'inherit' }}>
                        {row.map((cell: string, j: number) => (
                          <TableCell key={j} align={j === 0 ? 'left' : 'right'}>{cell}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}

          {/* Сравнение с пузырями */}
          {caseData.scenario_data?.bubble_comparison && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>🫧 Сравнение с пузырями</Typography>
              <Divider sx={{ mb: 2 }} />
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'primary.light' }}>
                      {caseData.scenario_data.bubble_comparison.headers.map((h: string, i: number) => (
                        <TableCell key={i} align={i === 0 ? 'left' : 'right'}><strong>{h}</strong></TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {caseData.scenario_data.bubble_comparison.rows.map((row: string[], i: number) => (
                      <TableRow key={i} sx={{ bgcolor: i % 2 === 1 ? 'action.hover' : 'inherit' }}>
                        {row.map((cell: string, j: number) => (
                          <TableCell key={j} align={j === 0 ? 'left' : 'right'}>{cell}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}

          {/* Динамика IPO */}
          {caseData.scenario_data?.ipo_trend && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>📈 Динамика IPO</Typography>
              <Divider sx={{ mb: 2 }} />
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'primary.light' }}>
                      {caseData.scenario_data.ipo_trend.headers.map((h: string, i: number) => (
                        <TableCell key={i} align={i === 0 ? 'left' : 'right'}><strong>{h}</strong></TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {caseData.scenario_data.ipo_trend.rows.map((row: string[], i: number) => (
                      <TableRow key={i} sx={{ bgcolor: i % 2 === 1 ? 'action.hover' : 'inherit' }}>
                        {row.map((cell: string, j: number) => (
                          <TableCell key={j} align={j === 0 ? 'left' : 'right'}>{cell}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}

          {/* Динамика кредитования */}
          {caseData.scenario_data?.lending_trend && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>💰 Динамика кредитования</Typography>
              <Divider sx={{ mb: 2 }} />
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'primary.light' }}>
                      {caseData.scenario_data.lending_trend.headers.map((h: string, i: number) => (
                        <TableCell key={i} align={i === 0 ? 'left' : 'right'}><strong>{h}</strong></TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {caseData.scenario_data.lending_trend.rows.map((row: string[], i: number) => (
                      <TableRow key={i} sx={{ bgcolor: i % 2 === 1 ? 'action.hover' : 'inherit' }}>
                        {row.map((cell: string, j: number) => (
                          <TableCell key={j} align={j === 0 ? 'left' : 'right'}>{cell}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}

          {/* Рыночные данные */}
          {caseData.scenario_data?.market_data && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>📊 Рыночные данные</Typography>
              <Divider sx={{ mb: 2 }} />
              <TableContainer>
                <Table size="small">
                  <TableBody>
                    {Object.entries(caseData.scenario_data.market_data).map(([key, value]) => (
                      <TableRow key={key}>
                        <TableCell sx={{ fontWeight: 500 }}>{key}</TableCell>
                        <TableCell align="right"><strong>{String(value)}</strong></TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}

          {/* Reddit Sentiment */}
          {caseData.scenario_data?.reddit_sentiment && (
            <Paper sx={{ p: 3, mb: 3, bgcolor: 'info.light', color: 'info.contrastText' }}>
              <Typography variant="h6" gutterBottom fontWeight="bold">💬 Reddit Sentiment (r/wallstreetbets)</Typography>
              <Divider sx={{ mb: 2, bgcolor: 'rgba(255,255,255,0.3)' }} />
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'info.main' }}>
                      {caseData.scenario_data.reddit_sentiment.headers.map((h: string, i: number) => (
                        <TableCell key={i} align={i === 0 ? 'left' : 'right'} sx={{ color: 'info.contrastText', fontWeight: 'bold' }}>
                          {h}
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {caseData.scenario_data.reddit_sentiment.rows.map((row: string[], i: number) => (
                      <TableRow key={i} sx={{ bgcolor: i % 2 === 1 ? 'action.hover' : 'inherit' }}>
                        {row.map((cell: string, j: number) => (
                          <TableCell key={j} align={j === 0 ? 'left' : 'right'} sx={{ color: 'info.contrastText' }}>{cell}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}

          {/* Ключевые события */}
          {caseData.scenario_data?.key_events && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>📅 Ключевые события</Typography>
              <Divider sx={{ mb: 2 }} />
              {caseData.scenario_data.key_events.map((event: any, i: number) => (
                <Box key={i} sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: i < caseData.scenario_data.key_events.length - 1 ? '1px solid #eee' : 'none' }}>
                  <Typography variant="body2" fontWeight="bold">{event.date}</Typography>
                  <Typography variant="body2">{event.event}</Typography>
                </Box>
              ))}
            </Paper>
          )}
        </Grid>
      </Grid>

      {/* Решение */}
      <Paper sx={{ p: 3, mt: 3, mb: 3, bgcolor: 'action.hover' }}>
        <Typography variant="h5" gutterBottom fontWeight="bold">🎯 Ваше решение</Typography>
        <Divider sx={{ mb: 2 }} />
        <RadioGroup value={selectedDecision} onChange={(e) => setSelectedDecision(e.target.value)} sx={{ mb: 2 }}>
          {decisionOptions.map((opt: any) => (
            <FormControlLabel
              key={opt.id}
              value={opt.id}
              control={<Radio />}
              sx={{ display: 'flex', alignItems: 'flex-start', mb: 2, p: 1.5, borderRadius: 1, bgcolor: 'background.paper', width: '100%' }}
              label={
                <Box>
                  <Typography fontWeight="bold">{opt.label}</Typography>
                  <Typography variant="body2" color="text.secondary">{opt.description}</Typography>
                </Box>
              }
            />
          ))}
        </RadioGroup>
        {!submitted ? (
          <Button variant="contained" size="large" onClick={handleSubmit} disabled={!selectedDecision} fullWidth>Отправить решение</Button>
        ) : (
          <Box>
            <Alert severity={result?.is_correct ? 'success' : 'warning'} sx={{ mt: 2, mb: 2 }}>
              <Typography variant="h6" fontWeight="bold">{result?.is_correct ? 'Правильно!' : 'Неверно'}</Typography>
              <Box sx={{ mt: 1 }}>
                {renderMarkdown(result?.explanation || '')}
              </Box>
              {result?.points_earned > 0 && <Chip label={`+${result.points_earned} баллов`} color="success" sx={{ mt: 2, mr: 1 }} />}
            </Alert>
            <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
              <Button variant="outlined" onClick={() => navigate('/cases')} fullWidth>К кейсам</Button>
              <Button variant="contained" onClick={() => { setSubmitted(false); setSelectedDecision(''); }} fullWidth>Попробовать снова</Button>
            </Box>
          </Box>
        )}
      </Paper>
    </Container>
  )
}
