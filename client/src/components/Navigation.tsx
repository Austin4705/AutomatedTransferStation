import { NavLink } from 'react-router-dom';

const Navigation = () => {
  return (
    <nav className="horizontal-navigation bg-gray-700 py-2 px-4">
      <ul className="flex space-x-6 justify-center">
        <li>
          <NavLink 
            to="/dashboard" 
            className={({ isActive }) => 
              isActive ? "nav-link active font-bold" : "nav-link hover:text-gray-300"
            }
          >
            Dashboard
          </NavLink>
        </li>
        <li>
          <NavLink 
            to="/camera" 
            className={({ isActive }) => 
              isActive ? "nav-link active font-bold" : "nav-link hover:text-gray-300"
            }
          >
            Camera
          </NavLink>
        </li>
        <li>
          <NavLink 
            to="/trace-over" 
            className={({ isActive }) => 
              isActive ? "nav-link active font-bold" : "nav-link hover:text-gray-300"
            }
          >
            Trace Over
          </NavLink>
        </li>
        <li>
          <NavLink 
            to="/system-logs" 
            className={({ isActive }) => 
              isActive ? "nav-link active font-bold" : "nav-link hover:text-gray-300"
            }
          >
            System Logs
          </NavLink>
        </li>
        <li>
          <NavLink 
            to="/commands" 
            className={({ isActive }) => 
              isActive ? "nav-link active font-bold" : "nav-link hover:text-gray-300"
            }
          >
            Commands & Actions
          </NavLink>
        </li>
      </ul>
    </nav>
  );
}

export default Navigation; 