import { Box, Container, Typography, Link } from '@mui/material'

export default function Footer() {
  return (
    <Box
      component="footer"
      sx={{
        bgcolor: 'background.paper',
        borderTop: '1px solid',
        borderColor: 'divider',
        py: 3,
        mt: 'auto'
      }}
    >
      <Container maxWidth="lg">
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            © 2026 InvestEdu. Платформа для обучения инвестициям
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            GIF via GIPHY
          </Typography>
        </Box>
      </Container>
    </Box>
  )
}
