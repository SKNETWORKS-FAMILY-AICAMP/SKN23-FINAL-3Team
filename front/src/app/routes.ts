import { createBrowserRouter } from "react-router";
import HomePage from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";
import { OAuthCallbackPage } from "./pages/OAuthCallbackPage";
import Step2Page from "./pages/Step2Page";
import MyPage from "./pages/MyPage";
import CalendarPage from "./pages/CalendarPage";
import PlaceFavoritesPage from "./pages/PlaceFavoritesPage";
import { RootLayout } from "./layouts/RootLayout";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: RootLayout,
    children: [
      { index: true, Component: HomePage },
      { path: "home", Component: HomePage },
      { path: "login", Component: LoginPage },
      { path: "oauth/callback", Component: OAuthCallbackPage },
      { path: "calendar", Component: CalendarPage },
      { path: "place-favorites", Component: PlaceFavoritesPage },
      { path: "step", Component: Step2Page },
      { path: "mypage", Component: MyPage },
    ],
  },
]);