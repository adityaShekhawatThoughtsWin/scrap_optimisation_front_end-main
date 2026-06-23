import { orderPlanData, scrapAvailabilityData } from "../../staticData";
import CustomTable from "./CustomTable";
import CustomTableWithData from "./CustomTableWithData";
import ProductionStats from "./ProductionStats";

function Home() {
    return (
        <div className="px-6 py-4">
            <ProductionStats />
            <CustomTableWithData title="ORDER PLAN" data={orderPlanData} />
            <CustomTableWithData title="SCRAP AVAILABILITY" data={scrapAvailabilityData} />
            <CustomTable title="Upload Your Excel File Here" />
        </div>
    )
}
export default Home;
