import { RouterProvider, createBrowserRouter } from "react-router";
import { routeList } from "./routes";

export default function App() {
  return <RouterProvider router={createBrowserRouter(routeList)} />;
}
