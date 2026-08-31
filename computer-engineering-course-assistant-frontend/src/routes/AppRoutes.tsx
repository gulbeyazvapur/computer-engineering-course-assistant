import { Route, Routes } from "react-router-dom";
import AppLayout from "../components/layout/AppLayout";
import AboutPage from "../pages/AboutPage";
import ChatPage from "../pages/ChatPage";
import CoursesPage from "../pages/CoursesPage";
import DocumentsPage from "../pages/DocumentsPage";
import NotFoundPage from "../pages/NotFoundPage";

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<ChatPage />} />
        <Route path="/courses" element={<CoursesPage />} />
        <Route path="/documents" element={<DocumentsPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
