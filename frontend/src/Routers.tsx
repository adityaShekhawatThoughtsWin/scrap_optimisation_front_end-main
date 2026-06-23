import { Navigate, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Home from "./components/dashboard/Home";
import Input from "./components/dashboard/Input";
function Routers() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" />} />
      <Route path="/dashboard" element={<Dashboard />} >
        <Route index element={<Home />} />
        <Route path="input" element={<Input />} />
      </Route>
    </Routes>
  )
}

export default Routers;