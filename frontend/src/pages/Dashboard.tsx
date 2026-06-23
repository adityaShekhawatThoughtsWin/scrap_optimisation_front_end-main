import { Navbar } from "../components/dashboard/Navbar";
import UploadFile from "./UploadFile";
export default function Dashboard() {
  return (
    <div>
      <Navbar />
      {/* <Tabs rightComponent={<DatePicker />}/>
      <Outlet /> */}
      <UploadFile />
    </div>
  );
}