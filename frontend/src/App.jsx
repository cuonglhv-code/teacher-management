import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline, AppBar, Toolbar, Typography, Button, Box, Container } from '@mui/material';
import TeacherList from './pages/TeacherList';
import TeacherDetail from './pages/TeacherDetail';
import ClassList from './pages/ClassList';
import ClassDetail from './pages/ClassDetail';
import RoomList from './pages/RoomList';
import CentreDashboard from './pages/CentreDashboard';
import CentreTeachers from './pages/CentreTeachers';
import CentreClasses from './pages/CentreClasses';
import CentreRooms from './pages/CentreRooms';
import CentreTimetable from './pages/CentreTimetable';
import WorkloadDashboard from './pages/WorkloadDashboard';
import HRDashboard from './pages/HRDashboard';
import ReportsPage from './pages/ReportsPage';
import Home from './pages/Home';

const theme = createTheme({
  palette: {
    primary: { main: '#1565c0' },
    secondary: { main: '#f57c00' },
  },
});

const navItems = [
  { label: 'Teachers', path: '/teachers' },
  { label: 'Classes', path: '/classes' },
  { label: 'Rooms', path: '/rooms' },
];

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" sx={{ flexGrow: 1, textDecoration: 'none', color: 'inherit' }}
              component={Link} to="/">
              JTWMS
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              {navItems.map((item) => (
                <Button key={item.path} color="inherit" component={Link} to={item.path}>
                  {item.label}
                </Button>
              ))}
            </Box>
          </Toolbar>
        </AppBar>

        <Container maxWidth="lg" sx={{ mt: 2 }}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/teachers" element={<TeacherList />} />
            <Route path="/teachers/:id" element={<TeacherDetail />} />
            <Route path="/classes" element={<ClassList />} />
            <Route path="/classes/:id" element={<ClassDetail />} />
            <Route path="/rooms" element={<RoomList />} />
            <Route path="/centres/:id/dashboard" element={<CentreDashboard />} />
            <Route path="/centres/:id/teachers" element={<CentreTeachers />} />
            <Route path="/centres/:id/classes" element={<CentreClasses />} />
            <Route path="/centres/:id/rooms" element={<CentreRooms />} />
            <Route path="/centres/:id/timetable" element={<CentreTimetable />} />
            <Route path="/centres/:id/workload" element={<WorkloadDashboard />} />
            <Route path="/centres/:id/availability" element={<AvailabilityEditor />} />
            <Route path="/hr" element={<HRDashboard />} />
            <Route path="/hr/:id" element={<HRDashboard />} />
            <Route path="/reports" element={<ReportsPage />} />
          </Routes>
        </Container>
      </Router>
    </ThemeProvider>
  );
}

export default App;
