import Layout from "./components/Layout";
import HomeScreen from "./screens/home/HomeScreen";
import PlantDetailScreen from "./screens/plant-detail/PlantDetailScreen";
import HistoryScreen from "./screens/history/HistoryScreen";
import DiagnosisHistoryScreen from "./screens/diagnosis-history/DiagnosisHistoryScreen";
import PlantSetupScreen from "./screens/plant-setup/PlantSetupScreen";
import DevicesScreen from "./screens/devices/DevicesScreen";
import AddDeviceScreen from "./screens/add-device/AddDeviceScreen";
import AccountScreen from "./screens/account/AccountScreen";
import HelpScreen from "./screens/help/HelpScreen";
import LoginScreen from "./screens/auth/LoginScreen";
import SignupScreen from "./screens/auth/SignupScreen";

// One route per 13.1 screen, with the folder names and routes from the C1 card,
// so later checkpoints never edit this list to add a screen. App.tsx turns this
// list into the router.
export const routeList = [
  {
    element: <Layout />,
    children: [
      { path: "/", element: <HomeScreen /> },
      { path: "/plants/:plantId", element: <PlantDetailScreen /> },
      { path: "/plants/:plantId/history", element: <HistoryScreen /> },
      { path: "/plants/:plantId/diagnoses", element: <DiagnosisHistoryScreen /> },
      { path: "/plants/new", element: <PlantSetupScreen /> },
      { path: "/devices", element: <DevicesScreen /> },
      { path: "/devices/add", element: <AddDeviceScreen /> },
      { path: "/account", element: <AccountScreen /> },
      { path: "/help", element: <HelpScreen /> },
    ],
  },
  { path: "/login", element: <LoginScreen /> },
  { path: "/signup", element: <SignupScreen /> },
];
