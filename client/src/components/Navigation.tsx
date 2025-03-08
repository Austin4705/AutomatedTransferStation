import { NavLink } from 'react-router-dom';

const Navigation = () => {
  return (
    <nav className="top-navigation bg-gray-700">
      <ul className="flex px-4 py-2">
        <li className="mr-6">
          <NavLink 
            to="/overview" 
            className={({ isActive }) => 
              isActive ? "nav-link active font-bold" : "nav-link hover:text-gray-300"
            }
          >
            Overview
          </NavLink>
        </li>
        <li className="mr-6">
          <NavLink 
            to="/camera" 
            className={({ isActive }) => 
              isActive ? "nav-link active font-bold" : "nav-link hover:text-gray-300"
            }
          >
            Camera
          </NavLink>
        </li>
        <li className="mr-6">
          <NavLink 
            to="/trace-over" 
            className={({ isActive }) => 
              isActive ? "nav-link active font-bold" : "nav-link hover:text-gray-300"
            }
          >
            Trace Over
          </NavLink>
        </li>
        <li className="mr-6">
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