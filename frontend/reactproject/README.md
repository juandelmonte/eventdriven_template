# Event-Driven Architecture Frontend

This is the React frontend for the Event-Driven Architecture Template. It communicates with the Django backend and receives real-time task updates via WebSockets.

## Technology Stack

- **React**: UI library
- **Vite**: Build tool and development server
- **React Router**: For client-side routing
- **WebSockets**: For real-time communication

## Available Scripts

In the project directory, you can run:

### `npm start` or `npm run dev`

Runs the app in development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will automatically reload when you make changes.\
You will see any lint errors in the console.

### `npm test`

Runs the test suite using Vitest.

### `npm run test:watch`

Launches the test runner in the interactive watch mode.

### `npm run build`

Builds the app for production to the `dist` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you're on your own.

You don't have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn't feel obligated to use this feature. However we understand that this tool wouldn't be useful if you couldn't customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

## Project Structure

- `src/components/`: React components
  - `Dashboard.js`: Main user interface after login
  - `Login.js`: Authentication component
  - `ProtectedRoute.js`: Route guard for authenticated routes
  - `Register.js`: User registration component
  - `ReverseStringTask.js`: Task submission component
  - `TaskList.js`: Displays list of tasks and results

- `src/services/`: API and WebSocket services
  - `api.js`: REST API client
  - `config.js`: Application configuration
  - `websocket.js`: WebSocket client for real-time updates

## Learn More

- [Vite Documentation](https://vitejs.dev/guide/)
- [React Documentation](https://reactjs.org/)
- [WebSockets API](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
