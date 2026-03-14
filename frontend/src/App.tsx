import { Routes, Route } from 'react-router-dom'
import { Box } from '@mui/material'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import HomePage from './pages/HomePage'
import CoursesPage from './pages/CoursesPage'
import CasesPage from './pages/CasesPage'
import LessonPage from './pages/LessonPage'
import CaseDetailPage from './pages/CaseDetailPage'
import LessonViewPage from './pages/LessonViewPage'
import AIAssistantPage from './pages/AIAssistantPage'
import GlossaryPage from './pages/GlossaryPage'

function App() {
  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', display: 'flex', flexDirection: 'column' }}>
      <Navbar />
      <Box component="main" sx={{ pt: { xs: 7, sm: 8 }, flex: 1 }}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/courses" element={<CoursesPage />} />
          <Route path="/courses/:moduleId" element={<LessonPage />} />
          <Route path="/courses/:moduleId/lesson/:lessonId" element={<LessonViewPage />} />
          <Route path="/cases" element={<CasesPage />} />
          <Route path="/cases/:caseId" element={<CaseDetailPage />} />
          <Route path="/ai-assistant" element={<AIAssistantPage />} />
          <Route path="/glossary" element={<GlossaryPage />} />
        </Routes>
      </Box>
      <Footer />
    </Box>
  )
}

export default App
