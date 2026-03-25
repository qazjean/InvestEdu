import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  Paper,
  Alert,
  Divider,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  TableHead,
  Stepper,
  Step,
  StepLabel,
  TextField,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import ArrowForwardIcon from '@mui/icons-material/ArrowForward'
import QuizIcon from '@mui/icons-material/Quiz'
import CalculateIcon from '@mui/icons-material/Calculate'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import LightbulbIcon from '@mui/icons-material/Lightbulb'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import ErrorIcon from '@mui/icons-material/Error'
import FormatQuoteIcon from '@mui/icons-material/FormatQuote'
import CodeIcon from '@mui/icons-material/Code'
import PetsIcon from '@mui/icons-material/Pets'

// Калькулятор сложного процента
function CompoundCalculator() {
  const [values, setValues] = useState({ initial: 10000, monthly: 500, rate: 10, years: 30 })
  const [result, setResult] = useState<any>(null)
  const calculate = () => {
    const r = values.rate / 100 / 12
    const n = values.years * 12
    const fvInitial = values.initial * Math.pow(1 + r, n)
    const fvMonthly = values.monthly * ((Math.pow(1 + r, n) - 1) / r)
    const total = fvInitial + fvMonthly
    const invested = values.initial + (values.monthly * n)
    setResult({ total: Math.round(total), invested: Math.round(invested), interest: Math.round(total - invested) })
  }
  useEffect(() => { calculate() }, [values])
  return (
    <Paper sx={{ p: 3, mt: 2, bgcolor: 'rgba(33, 150, 243, 0.08)', borderRadius: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}><CalculateIcon color="primary" /><Typography variant="h6" sx={{ fontWeight: 700 }}>Калькулятор сложного процента</Typography></Box>
      <Grid container spacing={2}>
        <Grid item xs={6} sm={3}><TextField label="Начальная ($)" type="number" value={values.initial} onChange={(e) => setValues({...values, initial: Number(e.target.value)})} fullWidth size="small" /></Grid>
        <Grid item xs={6} sm={3}><TextField label="В месяц ($)" type="number" value={values.monthly} onChange={(e) => setValues({...values, monthly: Number(e.target.value)})} fullWidth size="small" /></Grid>
        <Grid item xs={6} sm={3}><TextField label="Ставка (%)" type="number" value={values.rate} onChange={(e) => setValues({...values, rate: Number(e.target.value)})} fullWidth size="small" /></Grid>
        <Grid item xs={6} sm={3}><TextField label="Лет" type="number" value={values.years} onChange={(e) => setValues({...values, years: Number(e.target.value)})} fullWidth size="small" /></Grid>
      </Grid>
      {result && (
        <Grid container spacing={2} sx={{ mt: 2 }}>
          <Grid item xs={4}><Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'rgba(255,255,255,0.08)', borderRadius: 2 }}><Typography variant="caption" color="text.secondary">Вложено</Typography><Typography variant="h5" sx={{ fontWeight: 700 }}>${result.invested.toLocaleString()}</Typography></Paper></Grid>
          <Grid item xs={4}><Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'rgba(255,255,255,0.08)', borderRadius: 2 }}><Typography variant="caption" color="text.secondary">Проценты</Typography><Typography variant="h5" sx={{ fontWeight: 700, color: 'success.main' }}>${result.interest.toLocaleString()}</Typography></Paper></Grid>
          <Grid item xs={4}><Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'rgba(76, 175, 80, 0.15)', borderRadius: 2 }}><Typography variant="caption" color="text.secondary">Итого</Typography><Typography variant="h5" sx={{ fontWeight: 700, color: 'success.main' }}>${result.total.toLocaleString()}</Typography></Paper></Grid>
        </Grid>
      )}
    </Paper>
  )
}

// Котик-разделитель
function CatBreak({ cat }: { cat: any }) {
  if (!cat) return null
  const [imgError, setImgError] = useState(false)
  if (imgError || !cat.gif) {
    return (
      <Paper sx={{ p: 2, my: 3, bgcolor: 'rgba(255, 152, 0, 0.08)', borderRadius: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><PetsIcon color="warning" /><Typography variant="subtitle2" sx={{ fontWeight: 700 }}>Кот-Инвестор:</Typography></Box>
        <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>{cat.caption}</Typography>
      </Paper>
    )
  }
  return (
    <Paper sx={{ p: 0, my: 3, bgcolor: 'rgba(255, 152, 0, 0.08)', borderRadius: 2, overflow: 'hidden' }}>
      <Grid container>
        <Grid item xs={12} sm={4}><Box component="img" src={cat.gif} alt={cat.alt} sx={{ width: '100%', height: 180, objectFit: 'cover' }} onError={() => setImgError(true)} /></Grid>
        <Grid item xs={12} sm={8}>
          <CardContent sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}><PetsIcon color="warning" /><Typography variant="subtitle2" sx={{ fontWeight: 700 }}>Кот-Инвестор:</Typography></Box>
            <Typography variant="body2" sx={{ fontStyle: 'italic' }}>{cat.caption}</Typography>
          </CardContent>
        </Grid>
      </Grid>
    </Paper>
  )
}

// Котик-реакция
function CatReaction({ isCorrect, gif }: { isCorrect: boolean; gif?: string }) {
  const [imgError, setImgError] = useState(false)
  if (imgError || !gif) return <Typography variant="caption" sx={{ display: 'block', mt: 1, color: isCorrect ? 'success.main' : 'error.main' }}>{isCorrect ? '🎉 Верно!' : '😿 Попробуй ещё раз'}</Typography>
  return (
    <Box sx={{ textAlign: 'center', my: 2 }}>
      <Box component="img" src={gif} alt={isCorrect ? "Котик празднует" : "Грустный котик"} sx={{ width: '100%', maxWidth: 180, height: 'auto', borderRadius: 2 }} onError={() => setImgError(true)} />
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>{isCorrect ? "🎉 Котик доволен!" : "😿 Котик грустит, но ты справишься!"}</Typography>
    </Box>
  )
}

// Таблица риск/доходность
function RiskReturnTable({ assets, title }: { assets: any[]; title?: string }) {
  return (
    <Paper sx={{ mt: 3, mb: 3, p: 2, bgcolor: 'rgba(33, 150, 243, 0.08)', borderRadius: 2 }}>
      {title && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <CheckCircleIcon color="primary" />
          <Typography variant="h6" sx={{ fontWeight: 700, color: 'primary.main' }}>{title}</Typography>
        </Box>
      )}
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow sx={{ bgcolor: 'rgba(33, 150, 243, 0.2)' }}>
              <TableCell sx={{ fontWeight: 700, color: 'primary.main', fontSize: '0.95rem' }}>Актив</TableCell>
              <TableCell sx={{ fontWeight: 700, color: 'primary.main', fontSize: '0.95rem' }}>Риск</TableCell>
              <TableCell sx={{ fontWeight: 700, color: 'primary.main', fontSize: '0.95rem' }}>Доходность</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {assets.map((asset: any, i: number) => {
              // Определяем цвет для риска
              let chipColor: 'success' | 'warning' | 'error' = 'warning'
              if (asset.risk === 'Низкий' || asset.risk === 'Минимальный') chipColor = 'success'
              else if (asset.risk === 'Высокий') chipColor = 'error'
              
              return (
                <TableRow key={i} sx={{ '&:nth-of-type(even)': { bgcolor: 'rgba(33, 150, 243, 0.05)' }, '&:hover': { bgcolor: 'rgba(33, 150, 243, 0.1)' } }}>
                  <TableCell sx={{ fontWeight: 500, color: 'text.primary', py: 2 }}>{asset.name}</TableCell>
                  <TableCell>
                    <Chip 
                      label={asset.risk} 
                      size="small" 
                      color={chipColor}
                    />
                  </TableCell>
                  <TableCell sx={{ fontWeight: 700, color: 'text.primary', py: 2 }}>{asset.return}</TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  )
}

// Таблица выбора
function ChoiceTable({ data, title }: { data: any[]; title?: string }) {
  const keys = Object.keys(data[0])
  return (
    <Paper sx={{ mt: 3, mb: 3, p: 2, bgcolor: 'rgba(33, 150, 243, 0.05)', borderRadius: 2, border: '1px solid rgba(33, 150, 243, 0.2)' }}>
      {title && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <CheckCircleIcon color="primary" />
          <Typography variant="h6" sx={{ fontWeight: 700, color: 'primary.main' }}>{title}</Typography>
        </Box>
      )}
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow sx={{ bgcolor: 'rgba(33, 150, 243, 0.2)' }}>
              {keys.map((key) => (
                <TableCell key={key} sx={{ fontWeight: 700, color: 'primary.main', fontSize: '0.95rem', borderBottom: '2px solid rgba(33, 150, 243, 0.3)', py: 2 }}>
                  {key === 'role' ? 'Роль' : key === 'function' ? 'Функция' : key === 'example' ? 'Пример' : key}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {data.map((row, i) => (
              <TableRow key={i} sx={{ '&:nth-of-type(even)': { bgcolor: 'rgba(33, 150, 243, 0.05)' }, '&:hover': { bgcolor: 'rgba(33, 150, 243, 0.1)' }, '& td': { py: 2 } }}>
                {keys.map((key) => (
                  <TableCell key={key} sx={{ fontWeight: 500, color: 'text.primary', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                    {row[key]}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  )
}

// Калькулятор дивидендной доходности
function DividendCalculator({ default_price = 200, default_dividend = 6 }: { default_price?: number; default_dividend?: number }) {
  const [price, setPrice] = useState(default_price)
  const [dividend, setDividend] = useState(default_dividend)
  const [yieldValue, setYieldValue] = useState<number>((default_dividend / default_price) * 100)

  useEffect(() => {
    const yieldCalc = (dividend / price) * 100
    setYieldValue(Math.round(yieldCalc * 100) / 100)
  }, [price, dividend])

  return (
    <Paper sx={{ p: 3, mt: 3, mb: 3, bgcolor: 'rgba(76, 175, 80, 0.08)', borderRadius: 2, border: '1px solid rgba(76, 175, 80, 0.3)' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <CalculateIcon color="success" />
        <Typography variant="h6" sx={{ fontWeight: 700, color: 'success.main' }}>Калькулятор дивидендной доходности</Typography>
      </Box>
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6}>
          <TextField
            label="Цена акции ($)"
            type="number"
            value={price}
            onChange={(e) => setPrice(Number(e.target.value))}
            fullWidth
            size="medium"
            InputProps={{ inputProps: { min: 1 } }}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            label="Годовой дивиденд ($)"
            type="number"
            value={dividend}
            onChange={(e) => setDividend(Number(e.target.value))}
            fullWidth
            size="medium"
            InputProps={{ inputProps: { min: 0 } }}
          />
        </Grid>
      </Grid>
      <Box sx={{ mt: 3, p: 2, bgcolor: 'rgba(76, 175, 80, 0.15)', borderRadius: 2, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>Дивидендная доходность</Typography>
        <Typography variant="h3" sx={{ fontWeight: 800, color: 'success.main' }}>
          {yieldValue.toFixed(2)}%
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
          Формула: (Дивиденд / Цена) × 100%
        </Typography>
      </Box>
    </Paper>
  )
}

// Калькулятор доходности облигации (YTM)
function BondCalculator({ default_face_value = 1000, default_coupon = 5, default_price = 950, default_years = 5 }: { default_face_value?: number; default_coupon?: number; default_price?: number; default_years?: number }) {
  const [faceValue, setFaceValue] = useState(default_face_value)
  const [couponRate, setCouponRate] = useState(default_coupon)
  const [price, setPrice] = useState(default_price)
  const [years, setYears] = useState(default_years)
  const [ytm, setYtm] = useState<number>(0)
  const [annualCoupon, setAnnualCoupon] = useState<number>(0)
  const [totalReturn, setTotalReturn] = useState<number>(0)

  useEffect(() => {
    const coupon = faceValue * (couponRate / 100)
    setAnnualCoupon(coupon)
    
    // Приближённая формула YTM
    const ytmCalc = (coupon + (faceValue - price) / years) / ((faceValue + price) / 2) * 100
    setYtm(Math.round(ytmCalc * 100) / 100)
    
    const totalReturnCalc = (coupon * years) + (faceValue - price)
    setTotalReturn(Math.round(totalReturnCalc * 100) / 100)
  }, [faceValue, couponRate, price, years])

  return (
    <Paper sx={{ p: 3, mt: 3, mb: 3, bgcolor: 'rgba(33, 150, 243, 0.08)', borderRadius: 2, border: '1px solid rgba(33, 150, 243, 0.3)' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <CalculateIcon color="primary" />
        <Typography variant="h6" sx={{ fontWeight: 700, color: 'primary.main' }}>Калькулятор доходности облигации (YTM)</Typography>
      </Box>
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6}>
          <TextField
            label="Номинал ($)"
            type="number"
            value={faceValue}
            onChange={(e) => setFaceValue(Number(e.target.value))}
            fullWidth
            size="medium"
            InputProps={{ inputProps: { min: 100 } }}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            label="Купон (%)"
            type="number"
            value={couponRate}
            onChange={(e) => setCouponRate(Number(e.target.value))}
            fullWidth
            size="medium"
            InputProps={{ inputProps: { min: 0, step: 0.1 } }}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            label="Цена покупки ($)"
            type="number"
            value={price}
            onChange={(e) => setPrice(Number(e.target.value))}
            fullWidth
            size="medium"
            InputProps={{ inputProps: { min: 100 } }}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            label="Лет до погашения"
            type="number"
            value={years}
            onChange={(e) => setYears(Number(e.target.value))}
            fullWidth
            size="medium"
            InputProps={{ inputProps: { min: 1 } }}
          />
        </Grid>
      </Grid>
      <Grid container spacing={2} sx={{ mt: 2 }}>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'rgba(255,255,255,0.08)', borderRadius: 2 }}>
            <Typography variant="caption" color="text.secondary">Купон в год</Typography>
            <Typography variant="h6" sx={{ fontWeight: 700, color: 'text.primary' }}>${annualCoupon.toFixed(0)}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'rgba(255,255,255,0.08)', borderRadius: 2 }}>
            <Typography variant="caption" color="text.secondary">Общий доход</Typography>
            <Typography variant="h6" sx={{ fontWeight: 700, color: 'success.main' }}>${totalReturn.toFixed(0)}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'rgba(33, 150, 243, 0.15)', borderRadius: 2 }}>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>Доходность к погашению (YTM)</Typography>
            <Typography variant="h4" sx={{ fontWeight: 800, color: 'primary.main' }}>{ytm.toFixed(2)}%</Typography>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
              {price < faceValue ? '📈 Облигация с дисконтом' : price > faceValue ? '📉 Облигация с премией' : '✅ По номиналу'}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2, fontStyle: 'italic' }}>
        Формула: YTM ≈ (C + (F-P)/n) / ((F+P)/2), где C — купон, F — номинал, P — цена, n — лет
      </Typography>
    </Paper>
  )
}

// Рендеринг markdown с красивым оформлением
function MarkdownText({ text }: { text: string }) {
  const lines = text.split('\n')
  const elements: JSX.Element[] = []
  let inCodeBlock = false, codeLines: string[] = [], listItems: string[] = []
  let inTable = false, tableRows: string[][] = []
  
  const flushList = () => {
    if (listItems.length > 0) {
      elements.push(
        <Paper key={`list-${elements.length}`} sx={{ 
          my: 2, 
          p: 2, 
          bgcolor: 'rgba(33, 150, 243, 0.05)', 
          borderRadius: 2,
          border: '1px solid rgba(33, 150, 243, 0.2)'
        }}>
          <List sx={{ pl: 1 }}>
            {listItems.map((item, i) => {
              const isSubItem = item.trim().startsWith('→')
              const content = isSubItem ? item.trim().slice(1).trim() : item
              return (
                <ListItem key={i} sx={{ py: 0.8, pl: isSubItem ? 4 : 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <Box sx={{ 
                      width: 28, 
                      height: 28, 
                      borderRadius: '50%', 
                      bgcolor: isSubItem ? 'secondary.main' : 'primary.main',
                      color: 'white',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.9rem',
                      fontWeight: 700
                    }}>
                      {isSubItem ? '↳' : '•'}
                    </Box>
                  </ListItemIcon>
                  <ListItemText 
                    primary={formatInlineMarkdown(content)} 
                    primaryTypographyProps={{ variant: 'body1', sx: { lineHeight: 1.7, color: 'text.primary' } }} 
                  />
                </ListItem>
              )
            })}
          </List>
        </Paper>
      )
      listItems = []
    }
  }
  
  const formatInlineMarkdown = (text: string) => {
    const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g)
    return parts.map((part, j) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <Box key={j} component="span" sx={{ 
            color: '#4fc3f7', 
            fontWeight: 700,
            bgcolor: 'rgba(79, 195, 247, 0.1)',
            px: 0.5,
            py: 0.2,
            borderRadius: 1
          }}>
            {part.slice(2, -2)}
          </Box>
        )
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <Box key={j} component="code" sx={{ 
            backgroundColor: 'rgba(255,255,255,0.08)', 
            padding: '3px 8px', 
            borderRadius: 2, 
            fontFamily: '"Fira Code", "Consolas", monospace', 
            fontSize: '0.88rem',
            color: '#81c784',
            border: '1px solid rgba(129, 199, 132, 0.3)'
          }}>
            {part.slice(1, -1)}
          </Box>
        )
      }
      return part
    })
  }
  
  lines.forEach((line, index) => {
    const trimmedLine = line.trim()
    
    // Code blocks
    if (trimmedLine.startsWith('```')) {
      if (inCodeBlock) { 
        elements.push(
          <Paper key={`code-${index}`} sx={{ 
            p: 2, 
            my: 2, 
            bgcolor: '#0d1117', 
            borderRadius: 2, 
            border: '1px solid rgba(129, 199, 132, 0.3)',
            overflowX: 'auto' 
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
              <Box sx={{ 
                width: 12, 
                height: 12, 
                borderRadius: '50%', 
                bgcolor: '#ff5f56' 
              }} />
              <Box sx={{ 
                width: 12, 
                height: 12, 
                borderRadius: '50%', 
                bgcolor: '#ffbd2e' 
              }} />
              <Box sx={{ 
                width: 12, 
                height: 12, 
                borderRadius: '50%', 
                bgcolor: '#27c93f' 
              }} />
              <Typography variant="caption" sx={{ ml: 1, color: 'text.secondary', fontFamily: 'monospace' }}>CODE</Typography>
            </Box>
            <Typography variant="body2" sx={{ 
              fontFamily: '"Fira Code", "Consolas", monospace', 
              fontSize: '0.85rem', 
              lineHeight: 1.7, 
              color: '#a5d6a7', 
              whiteSpace: 'pre-wrap' 
            }}>
              {codeLines.join('\n')}
            </Typography>
          </Paper>
        )
        codeLines = []
        inCodeBlock = false 
      } else { 
        flushList()
        inCodeBlock = true 
      }
      return
    }
    if (inCodeBlock) { codeLines.push(line); return }
    
    // Empty line
    if (trimmedLine === '') { flushList(); return }
    
    // Horizontal rule
    if (trimmedLine === '---') {
      flushList()
      elements.push(
        <Box key={index} sx={{ 
          my: 4, 
          height: '2px', 
          bgcolor: 'linear-gradient(90deg, transparent, rgba(79, 195, 247, 0.5), transparent)',
          background: 'linear-gradient(90deg, transparent, rgba(79, 195, 247, 0.5), transparent)'
        }} />
      )
      return
    }
    
    // Headers с красивым оформлением
    if (trimmedLine.startsWith('### ')) { 
      flushList()
      elements.push(
        <Typography key={index} variant="h5" sx={{ 
          mt: 4, 
          mb: 2, 
          fontWeight: 800, 
          color: 'primary.main',
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
          fontSize: '1.5rem'
        }}>
          <Box sx={{ 
            width: 8, 
            height: 28, 
            bgcolor: 'primary.main',
            borderRadius: 1
          }} />
          {trimmedLine.slice(4)}
        </Typography>
      )
      return 
    }
    if (trimmedLine.startsWith('## ')) { 
      flushList()
      elements.push(
        <Typography key={index} variant="h4" sx={{ 
          mt: 4, 
          mb: 2.5, 
          fontWeight: 800, 
          color: 'text.primary',
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          fontSize: '1.8rem',
          pb: 1,
          borderBottom: '3px solid rgba(79, 195, 247, 0.3)'
        }}>
          <Box sx={{ 
            width: 10, 
            height: 32, 
            bgcolor: 'primary.main',
            borderRadius: 1.5
          }} />
          {trimmedLine.slice(3)}
        </Typography>
      )
      return 
    }
    if (trimmedLine.startsWith('# ')) { 
      flushList()
      elements.push(
        <Typography key={index} variant="h3" sx={{ 
          mt: 4, 
          mb: 3, 
          fontWeight: 800, 
          color: 'text.primary',
          fontSize: '2.2rem',
          background: 'linear-gradient(135deg, #4fc3f7 0%, #81c784 100%)',
          backgroundClip: 'text',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          pb: 1
        }}>
          {trimmedLine.slice(2)}
        </Typography>
      )
      return 
    }
    if (trimmedLine.startsWith('#### ')) { 
      flushList()
      elements.push(
        <Typography key={index} variant="h6" sx={{ 
          mt: 3, 
          mb: 1.5, 
          fontWeight: 700, 
          color: 'secondary.main',
          fontSize: '1.1rem',
          display: 'flex',
          alignItems: 'center',
          gap: 1
        }}>
          <Box sx={{ 
            width: 6, 
            height: 6, 
            borderRadius: '50%', 
            bgcolor: 'secondary.main' 
          }} />
          {trimmedLine.slice(4)}
        </Typography>
      )
      return 
    }
    
    // Blockquote с красивым оформлением
    if (trimmedLine.startsWith('> ')) { 
      flushList()
      elements.push(
        <Paper key={index} sx={{ 
          p: 2.5, 
          my: 2.5, 
          bgcolor: 'rgba(33, 150, 243, 0.08)', 
          borderRadius: 2, 
          borderLeft: '5px solid #4fc3f7',
          background: 'linear-gradient(90deg, rgba(33, 150, 243, 0.12) 0%, rgba(33, 150, 243, 0.05) 100%)'
        }}>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
            <FormatQuoteIcon sx={{ color: 'primary.main', mt: 0.3, fontSize: 28 }} />
            <Typography variant="body1" sx={{ 
              fontStyle: 'italic', 
              lineHeight: 1.8,
              color: 'text.primary',
              fontSize: '0.98rem'
            }}>
              {formatInlineMarkdown(trimmedLine.slice(2))}
            </Typography>
          </Box>
        </Paper>
      )
      return 
    }
    
    // Tables (render markdown tables)
    if (trimmedLine.startsWith('|') && trimmedLine.endsWith('|')) {
      flushList()
      // Проверяем, это заголовок таблицы или разделитель
      if (trimmedLine.includes('|---') || trimmedLine.includes('| -')) {
        return // пропускаем строку разделителя
      }
      // Это строка таблицы - добавляем в таблицу
      const cells = trimmedLine.split('|').filter(cell => cell.trim()).map(cell => cell.trim())
      if (cells.length > 0) {
        // Если это первая строка таблицы, создаём TableContainer
        if (!inTable) {
          inTable = true
          tableRows = []
        }
        tableRows.push(cells)
      }
      return
    }
    
    // Если вышли из таблицы (пустая строка или другой контент)
    if (inTable && trimmedLine === '') {
      flushList()
      if (tableRows.length > 0) {
        elements.push(
          <TableContainer key={`table-${elements.length}`} sx={{ mt: 2, mb: 2, borderRadius: 2, border: '1px solid rgba(255,255,255,0.1)' }}>
            <Table>
              {tableRows.length > 1 && (
                <TableHead>
                  <TableRow sx={{ bgcolor: 'rgba(33, 150, 243, 0.2)' }}>
                    {tableRows[0].map((cell, i) => (
                      <TableCell key={i} sx={{ fontWeight: 700, color: 'primary.main', fontSize: '0.95rem', borderBottom: '2px solid rgba(33, 150, 243, 0.3)', py: 2 }}>
                        {formatInlineMarkdown(cell)}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
              )}
              <TableBody>
                {tableRows.slice(1).map((row, i) => (
                  <TableRow key={i} sx={{ '&:nth-of-type(even)': { bgcolor: 'rgba(33, 150, 243, 0.05)' }, '&:hover': { bgcolor: 'rgba(33, 150, 243, 0.1)' } }}>
                    {row.map((cell, j) => (
                      <TableCell key={j} sx={{ fontWeight: 500, color: 'text.primary', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 2 }}>
                        {formatInlineMarkdown(cell)}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )
        tableRows = []
        inTable = false
      }
      return
    }
    
    // List items (-, •, numbers, →)
    if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('• ') || trimmedLine.match(/^\d+\.\s/) || trimmedLine.startsWith('→')) { 
      listItems.push(trimmedLine.replace(/^[-•]\s|^(\d+\.\s)|^→\s?/, ''))
      return 
    }
    
    // Regular paragraph
    flushList()
    elements.push(
      <Typography key={index} variant="body1" sx={{ 
        mb: 2, 
        lineHeight: 1.8,
        color: 'text.primary',
        fontSize: '1rem'
      }}>
        {formatInlineMarkdown(trimmedLine)}
      </Typography>
    )
  })

  // Обработка таблицы в конце текста
  if (inTable && tableRows.length > 0) {
    elements.push(
      <TableContainer key={`table-${elements.length}`} sx={{ mt: 2, mb: 2, borderRadius: 2, border: '1px solid rgba(255,255,255,0.1)' }}>
        <Table>
          {tableRows.length > 1 && (
            <TableHead>
              <TableRow sx={{ bgcolor: 'rgba(33, 150, 243, 0.2)' }}>
                {tableRows[0].map((cell, i) => (
                  <TableCell key={i} sx={{ fontWeight: 700, color: 'primary.main', fontSize: '0.95rem', borderBottom: '2px solid rgba(33, 150, 243, 0.3)', py: 2 }}>
                    {formatInlineMarkdown(cell)}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
          )}
          <TableBody>
            {tableRows.slice(1).map((row, i) => (
              <TableRow key={i} sx={{ '&:nth-of-type(even)': { bgcolor: 'rgba(33, 150, 243, 0.05)' }, '&:hover': { bgcolor: 'rgba(33, 150, 243, 0.1)' } }}>
                {row.map((cell, j) => (
                  <TableCell key={j} sx={{ fontWeight: 500, color: 'text.primary', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 2 }}>
                    {formatInlineMarkdown(cell)}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    )
  }

  flushList()
  return <Box>{elements}</Box>
}

// Квиз "Инвестиция или спекуляция"
function DecisionQuiz({ items }: { items: any[] }) {
  const [revealed, setRevealed] = useState<Record<number, boolean>>({})
  return (
    <Paper sx={{ p: 3, mt: 2, bgcolor: 'rgba(255, 152, 0, 0.08)', borderRadius: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}><AutoAwesomeIcon color="warning" /><Typography variant="h6" sx={{ fontWeight: 700 }}>Интерактив: Инвестиция или Спекуляция?</Typography></Box>
      <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>Определите тип каждого действия и нажмите, чтобы увидеть ответ:</Typography>
      {items.map((item, i) => (
        <Card key={i} sx={{ mb: 2, cursor: 'pointer', transition: 'transform 0.2s', '&:hover': { transform: 'translateY(-2px)', boxShadow: '0 4px 12px rgba(0,0,0,0.15)', borderColor: 'primary.main' }, border: '1px solid', borderColor: revealed[i] ? (item.is_investment ? 'success.main' : 'error.main') : 'rgba(255,255,255,0.1)' }}>
          <CardContent onClick={() => setRevealed({...revealed, [i]: !revealed[i]})}>
            <Typography variant="body1" sx={{ mb: 2 }}>{i + 1}. {item.text}</Typography>
            {revealed[i] && (<Alert severity={item.is_investment ? 'success' : 'error'}><Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>{item.is_investment ? '✅ ИНВЕСТИЦИЯ' : '❌ СПЕКУЛЯЦИЯ'}</Typography><Typography variant="body2" sx={{ whiteSpace: 'pre-line', lineHeight: 1.6 }}>{item.explanation}</Typography></Alert>)}
            {!revealed[i] && (<Chip label="📌 Нажмите для ответа" size="small" variant="outlined" />)}
          </CardContent>
        </Card>
      ))}
    </Paper>
  )
}

export default function LessonViewPage() {
  const { moduleId, lessonId } = useParams<{ moduleId: string; lessonId: string }>()
  const navigate = useNavigate()
  const [lesson, setLesson] = useState<any>(null)
  const [moduleTitle, setModuleTitle] = useState('')
  const [allLessons, setAllLessons] = useState<any[]>([])
  const [currentLessonIndex, setCurrentLessonIndex] = useState(-1)
  const [quizAnswers, setQuizAnswers] = useState<Record<number, number>>({})
  const [quizSubmitted, setQuizSubmitted] = useState(false)
  const [quizScore, setQuizScore] = useState<number | null>(null)
  const [activeChapter, setActiveChapter] = useState(0)
  const chapterRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Загружаем урок
    fetch(`/api/courses/lesson/${lessonId}`).then(r => r.json()).then(data => {
      setLesson(data)
      if (data.content?.chapters) setActiveChapter(0)
      
      // Проверяем, пройден ли уже этот урок
      const savedCompleted = localStorage.getItem('lessons_completed')
      const completed = savedCompleted ? JSON.parse(savedCompleted) : []
      const isCompleted = completed.includes(Number(data.id))
      
      // Сбрасываем состояние теста при загрузке нового урока
      setQuizSubmitted(false)
      setQuizScore(null)
      setQuizAnswers({})
      
      // Скролл к началу после загрузки контента
      setTimeout(() => window.scrollTo({ top: 0, behavior: 'smooth' }), 100)
    }).catch(err => console.error(err))
    
    // Загружаем все уроки модуля для навигации
    fetch(`/api/courses/modules/${moduleId}/lessons`).then(r => r.json()).then(data => {
      setAllLessons(data)
      const index = data.findIndex((l: any) => l.id === parseInt(lessonId || '0'))
      setCurrentLessonIndex(index)
      
      // Получаем название модуля из первого урока
      if (data.length > 0 && data[0].module) {
        setModuleTitle(data[0].module.title)
      }
    }).catch(err => console.error(err))
  }, [lessonId, moduleId])

  // Автоскролл к началу главы при переключении
  useEffect(() => {
    if (chapterRef.current) {
      chapterRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [activeChapter])

  const handleQuizAnswer = (questionIndex: number, answerIndex: number) => setQuizAnswers(prev => ({ ...prev, [questionIndex]: answerIndex }))

  const submitQuiz = () => {
    if (!lesson || !lesson.content?.quiz) return
    const questions = lesson.content.quiz.questions
    let correct = 0
    questions.forEach((q: any, i: number) => {
      const selectedIdx = quizAnswers[i]
      if (selectedIdx !== undefined && q.options[selectedIdx]?.is_correct) {
        correct++
      }
    })
    const score = Math.round((correct / questions.length) * 100)
    setQuizScore(score)
    setQuizSubmitted(true)
    
    // Сохраняем прогресс если тест пройден (≥70% = максимум 1 ошибка)
    if (score >= 70) {
      const moduleId = lesson.module_id
      const lessonId = Number(lesson.id) // Гарантируем число

      console.log('💾 Сохранение прогресса:', { moduleId, lessonId, score })

      // Получаем текущий прогресс
      const savedCompleted = localStorage.getItem('lessons_completed')
      const completed: number[] = savedCompleted ? JSON.parse(savedCompleted) : []

      console.log('   Текущие completed:', completed)

      // Добавляем урок если ещё не пройден
      if (!completed.includes(lessonId)) {
        completed.push(lessonId)
        localStorage.setItem('lessons_completed', JSON.stringify(completed))
        console.log('   ✅ Сохранено:', completed)

        // Отправляем событие обновления прогресса
        const event = new CustomEvent('lessonProgressUpdate', {
          detail: { moduleId, lessonId, score }
        })
        window.dispatchEvent(event)
      } else {
        console.log('   ⚠️ Урок уже пройден')
      }
    }
  }

  if (!lesson) return null

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: { xs: 4, sm: 6 } }}>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate(`/courses/${moduleId}`)} sx={{ mb: 2 }}>← Назад к модулю</Button>
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, flexWrap: 'wrap' }}><Chip label={`⏱️ ${lesson.duration_minutes} мин`} size="small" variant="outlined" /><Chip icon={<QuizIcon />} label={`${lesson.content?.quiz?.questions?.length || 0} вопросов`} size="small" color="primary" /></Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 2 }}>{lesson.title}</Typography>
          <Typography variant="body1" color="text.secondary">{lesson.description}</Typography>
        </Box>

        {lesson.content?.introduction && (
          <Paper sx={{ p: 3, mb: 3, bgcolor: 'rgba(33, 150, 243, 0.08)', borderRadius: 2 }}>
            <Typography variant="h6" sx={{ mb: 2, color: 'primary.main', fontWeight: 700 }}>{lesson.content.introduction.title}</Typography>
            {lesson.content.introduction.welcome_cat && <CatBreak cat={lesson.content.introduction.welcome_cat} />}
            <MarkdownText text={lesson.content.introduction.text} />
            {lesson.content.introduction.choice_table && <ChoiceTable data={lesson.content.introduction.choice_table} />}
            {lesson.content.introduction.learning_objectives && (
              <Paper sx={{ p: 2, mt: 2, bgcolor: 'rgba(33, 150, 243, 0.08)', borderRadius: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}><LightbulbIcon color="primary" /><Typography variant="subtitle2" sx={{ fontWeight: 700 }}>В этом уроке вы узнаете:</Typography></Box>
                <List dense sx={{ m: 0, pl: 1 }}>{lesson.content.introduction.learning_objectives.map((obj: string, i: number) => (<ListItem key={i} sx={{ py: 0.5 }}><ListItemIcon sx={{ minWidth: 32 }}><CheckCircleIcon color="primary" fontSize="small" /></ListItemIcon><ListItemText primary={obj} primaryTypographyProps={{ variant: 'body2' }} /></ListItem>))}</List>
              </Paper>
            )}
          </Paper>
        )}

        {lesson.content?.chapters?.map((chapter: any, chapterIndex: number) => (
          <Box key={chapter.chapter_number} ref={activeChapter === chapterIndex ? chapterRef : null} sx={{ display: chapterIndex === activeChapter ? 'block' : 'none' }}>
            <Card sx={{ mb: 3, borderRadius: 2 }}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h5" sx={{ mb: 3, fontWeight: 700, color: 'primary.main' }}>Глава {chapter.chapter_number}: {chapter.title}</Typography>
                {chapter.subsections?.map((subsection: any, subIndex: number) => (
                  <Box key={subIndex} sx={{ mb: 3 }}>
                    <Typography variant="h6" sx={{ mb: 2, fontWeight: 600, color: 'text.primary' }}>{subsection.title}</Typography>
                    <MarkdownText text={subsection.content} />
                  </Box>
                ))}
                {chapter.content && <MarkdownText text={chapter.content} />}
              </CardContent>
            </Card>
            {chapter.cat_break && <CatBreak cat={chapter.cat_break} />}
            {chapter.interactive && (
              <Box sx={{ mb: 3 }}>
                {chapter.interactive.type === 'decision_quiz' && <DecisionQuiz items={chapter.interactive.items} />}
                {chapter.interactive.type === 'compound_calculator' && <CompoundCalculator />}
                {chapter.interactive.type === 'risk_return_table' && <RiskReturnTable assets={chapter.interactive.assets} title={chapter.interactive.title} />}
                {chapter.interactive.type === 'choice_table' && <ChoiceTable data={chapter.interactive.data} title={chapter.interactive.title} />}
                {chapter.interactive.type === 'dividend_calculator' && <DividendCalculator default_price={chapter.interactive.default_price} default_dividend={chapter.interactive.default_dividend} />}
                {chapter.interactive.type === 'bond_calculator' && <BondCalculator default_face_value={chapter.interactive.default_face_value} default_coupon={chapter.interactive.default_coupon} default_price={chapter.interactive.default_price} default_years={chapter.interactive.default_years} />}
              </Box>
            )}
          </Box>
        ))}

        {lesson.content?.chapters && (
          <Box sx={{ mb: 4 }}>
            <Divider sx={{ my: 3 }} />
            <Stepper activeStep={activeChapter} alternativeLabel sx={{ mb: 3 }}>{lesson.content.chapters.map((chapter: any) => (<Step key={chapter.chapter_number}><StepLabel onClick={() => setActiveChapter(chapter.chapter_number - 1)} sx={{ cursor: 'pointer' }}><Typography variant="caption" sx={{ fontWeight: activeChapter === chapter.chapter_number - 1 ? 700 : 400 }}>Глава {chapter.chapter_number}</Typography></StepLabel></Step>))}</Stepper>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Button variant="outlined" disabled={activeChapter === 0} onClick={() => setActiveChapter(activeChapter - 1)} sx={{ px: 3 }}>← Назад</Button>
              <Button variant="contained" disabled={activeChapter === lesson.content.chapters.length - 1} onClick={() => setActiveChapter(activeChapter + 1)} sx={{ px: 3 }}>Далее →</Button>
            </Box>
          </Box>
        )}

        {lesson.content?.summary && (
          <Paper sx={{ p: 3, mb: 3, bgcolor: 'rgba(76, 175, 80, 0.08)', borderRadius: 2 }}>
            <Typography variant="h6" sx={{ mb: 2, color: 'success.main', display: 'flex', alignItems: 'center', gap: 1, fontWeight: 700 }}><CheckCircleIcon /> Итоги урока</Typography>
            <List sx={{ m: 0, pl: 0 }}>
              {(lesson.content.summary.key_points || lesson.content.summary.key_takeaways || []).map((item: string, i: number) => (
                <ListItem key={i} sx={{ py: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 32 }}><CheckCircleIcon color="success" fontSize="small" /></ListItemIcon>
                  <ListItemText primary={item} primaryTypographyProps={{ variant: 'body1' }} />
                </ListItem>
              ))}
            </List>
            {lesson.content.summary.common_mistakes && lesson.content.summary.common_mistakes.length > 0 && (<Alert severity="warning" sx={{ mt: 2, borderRadius: 2 }}><Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}><Typography variant="subtitle2" sx={{ fontWeight: 700 }}>Частые ошибки:</Typography></Box><List dense sx={{ m: 0, pl: 1 }}>{lesson.content.summary.common_mistakes.map((item: string, i: number) => (<ListItem key={i} sx={{ py: 0.3 }}><ListItemText primary={item} primaryTypographyProps={{ variant: 'body2' }} /></ListItem>))}</List></Alert>)}
          </Paper>
        )}

        {lesson.content?.summary?.final_cat && <CatBreak cat={lesson.content.summary.final_cat} />}

        {lesson.content?.quiz && (
          <Card sx={{ borderRadius: 2, mt: 3 }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h5" sx={{ mb: 1, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 1 }}>
                <QuizIcon /> {lesson.content.quiz.title || 'Проверка знаний'}
              </Typography>
              {lesson.content.quiz.intro && (
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  {lesson.content.quiz.intro}
                </Typography>
              )}
              
              {lesson.content.quiz.questions?.map((q: any, qIndex: number) => (
                <Box key={qIndex} sx={{ mb: 4, p: 2, borderRadius: 2, bgcolor: 'rgba(255,255,255,0.03)' }}>
                  <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600, fontSize: '1.05rem' }}>
                    {qIndex + 1}. {q.question}
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    {q.options.map((option: any, oIndex: number) => {
                      const optionText = typeof option === 'string' ? option : option.text
                      const isSelected = quizAnswers[qIndex] === oIndex
                      const isCorrect = option.is_correct === true
                      const showResult = quizSubmitted
                      
                      let bgColor = 'transparent'
                      let borderColor = 'rgba(255,255,255,0.2)'
                      
                      if (showResult && isSelected) {
                        bgColor = isCorrect ? 'success.main' : 'error.main'
                        borderColor = isCorrect ? 'success.main' : 'error.main'
                      } else if (isSelected) {
                        bgColor = 'primary.main'
                        borderColor = 'primary.main'
                      }
                      
                      return (
                        <Button
                          key={oIndex}
                          variant={isSelected ? 'contained' : 'outlined'}
                          onClick={() => handleQuizAnswer(qIndex, oIndex)}
                          disabled={quizSubmitted}
                          sx={{
                            justifyContent: 'flex-start',
                            textAlign: 'left',
                            height: 'auto',
                            py: 1.5,
                            px: 2,
                            borderRadius: 2,
                            bgcolor: bgColor,
                            borderColor: borderColor,
                            '&:hover': {
                              bgcolor: isSelected ? bgColor : 'rgba(255,255,255,0.08)',
                              borderColor: borderColor,
                            },
                          }}
                        >
                          <Typography variant="body1">{optionText}</Typography>
                        </Button>
                      )
                    })}
                  </Box>
                  {quizSubmitted && (
                    <Alert
                      severity={quizAnswers[qIndex] === q.options.findIndex((o: any) => o.is_correct) ? 'success' : 'error'}
                      sx={{ mt: 2, borderRadius: 2 }}
                    >
                      <Typography variant="body2" sx={{ mt: 0.5, whiteSpace: 'pre-line', lineHeight: 1.6 }}>
                        {q.explanation}
                      </Typography>
                    </Alert>
                  )}
                </Box>
              ))}
              
              <Divider sx={{ my: 3 }} />
              
              {!quizSubmitted ? (
                <Button
                  variant="contained"
                  size="large"
                  fullWidth
                  onClick={submitQuiz}
                  disabled={Object.keys(quizAnswers).length < (lesson.content.quiz.questions?.length || 0)}
                  sx={{ py: 1.5, borderRadius: 2, fontSize: '1rem' }}
                >
                  Показать результат
                </Button>
              ) : (
                <Box>
                  <Alert 
                    severity={quizScore! >= 70 ? 'success' : 'warning'} 
                    sx={{ borderRadius: 2, mb: 2 }}
                  >
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>
                      Ваш результат: {quizScore}%
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      {quizScore! >= 70 ? '🎉 Отлично! Материал усвоен.' : '📚 Рекомендуем повторить урок.'}
                    </Typography>
                  </Alert>
                  {lesson.content.quiz.cat_reaction && (
                    <CatReaction
                      isCorrect={quizScore! >= 70}
                      gif={quizScore! >= 70 
                        ? lesson.content.quiz.cat_reaction.success?.gif || lesson.content.quiz.cat_reaction.success
                        : lesson.content.quiz.cat_reaction.fail?.gif || lesson.content.quiz.cat_reaction.fail
                      }
                    />
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        )}

        {/* Навигация между уроками */}
        <Box sx={{ mt: 4, mb: 4 }}>
          <Divider sx={{ mb: 3 }} />
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Button
              variant="outlined"
              startIcon={<ArrowBackIcon />}
              disabled={currentLessonIndex <= 0}
              onClick={() => {
                const prevLesson = allLessons[currentLessonIndex - 1]
                if (prevLesson) navigate(`/courses/${moduleId}/lesson/${prevLesson.id}`)
              }}
              sx={{ px: 3, py: 1.5 }}
            >
              ← Предыдущий урок
            </Button>
            
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Урок {currentLessonIndex + 1} из {allLessons.length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {moduleTitle}
              </Typography>
            </Box>
            
            <Button
              variant="contained"
              endIcon={<ArrowForwardIcon />}
              disabled={currentLessonIndex >= allLessons.length - 1}
              onClick={() => {
                const nextLesson = allLessons[currentLessonIndex + 1]
                if (nextLesson) navigate(`/courses/${moduleId}/lesson/${nextLesson.id}`)
              }}
              sx={{ px: 3, py: 1.5 }}
            >
              Следующий урок →
            </Button>
          </Box>
        </Box>
      </Box>
    </Container>
  )
}
