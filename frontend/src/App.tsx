import { useEffect } from 'react';
import { RouterProvider } from 'react-router-dom';

import router from '@/router';
import { startBuildSync } from '@/utils/buildSync';

export default function App() {
  useEffect(() => startBuildSync(__APP_BUILD_ID__), []);

  return <RouterProvider router={router} />;
}
