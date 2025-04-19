// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Show React components after they're mounted
    setTimeout(() => {
        document.querySelectorAll('.react-mount').forEach(el => {
            el.classList.add('loaded');
        });
    }, 100);

    // Render React components
    renderNavbar();

    // Only render dashboard if we're on the dashboard page
    if (document.getElementById('react-dashboard')) {
        renderDashboard();
    }
});

// Navbar Component
function renderNavbar() {
    // Navbar Component
    const Navbar = () => {
        const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);
        const [activeDropdown, setActiveDropdown] = React.useState(null);
        const currentPath = window.location.pathname;

        // Close dropdowns when clicking outside
        React.useEffect(() => {
            function handleClickOutside(event) {
                if (activeDropdown && !event.target.closest('.dropdown')) {
                    setActiveDropdown(null);
                }
            }

            document.addEventListener('click', handleClickOutside);
            return () => {
                document.removeEventListener('click', handleClickOutside);
            };
        }, [activeDropdown]);

        // Toggle dropdown
        const toggleDropdown = (name) => {
            setActiveDropdown(activeDropdown === name ? null : name);
        };

        // Check if a path is active
        const isActive = (path) => {
            if (path === '/admin_dashboard/' && currentPath === '/admin_dashboard/') {
                return true;
            }
            if (path !== '/admin_dashboard/' && currentPath.includes(path)) {
                return true;
            }
            return false;
        };

        return (
            <header className="bg-gradient-to-r from-primary-700 to-primary-900 text-white shadow-md">
                <div className="max-w-7xl mx-auto px-4">
                    <div className="flex items-center justify-between h-16">
                        {/* Logo */}
                        <div className="flex items-center">
                            <a href="/admin_dashboard/" className="flex items-center group">
                                <div className="bg-white/10 p-2 rounded-lg mr-3 transition-all duration-300 group-hover:bg-white/20">
                                    <i className="fas fa-shield-alt text-xl"></i>
                                </div>
                                <div>
                                    <div className="font-bold text-lg">PRO-13</div>
                                    <div className="text-xs text-primary-200">Regional Information System</div>
                                </div>
                            </a>
                        </div>

                        {/* Desktop Navigation */}
                        <nav className="hidden md:flex items-center space-x-6">
                            <a
                                href="/admin_dashboard/"
                                className={`nav-link flex items-center px-3 py-2 rounded-md ${isActive('/admin_dashboard/') ? 'active text-white' : 'text-primary-100 hover:text-white'}`}
                            >
                                <i className="fas fa-home mr-2"></i>
                                Dashboard
                            </a>

                            <div className="dropdown relative">
                                <button
                                    onClick={() => toggleDropdown('data')}
                                    className={`nav-link flex items-center px-3 py-2 rounded-md ${isActive('/upload/') || isActive('/data_overview/') ? 'active text-white' : 'text-primary-100 hover:text-white'}`}
                                >
                                    <i className="fas fa-database mr-2"></i>
                                    Data
                                    <i className={`fas fa-chevron-down ml-2 text-xs transition-transform duration-200 ${activeDropdown === 'data' ? 'rotate-180' : ''}`}></i>
                                </button>
                                <div className={`dropdown-content absolute left-0 mt-2 w-48 rounded-md shadow-lg bg-white z-50 ${activeDropdown === 'data' ? 'show' : ''}`}>
                                    <a
                                        href="/upload/"
                                        className="block px-4 py-2 text-sm text-secondary-700 hover:bg-primary-50 hover:text-primary-700 rounded-t-md"
                                    >
                                        <i className="fas fa-upload mr-2 text-primary-500"></i>
                                        Upload Data
                                    </a>
                                    <a
                                        href="/data_overview/"
                                        className="block px-4 py-2 text-sm text-secondary-700 hover:bg-primary-50 hover:text-primary-700 rounded-b-md"
                                    >
                                        <i className="fas fa-table mr-2 text-primary-500"></i>
                                        Data Overview
                                    </a>
                                </div>
                            </div>

                            <div className="dropdown relative">
                                <button
                                    onClick={() => toggleDropdown('analytics')}
                                    className={`nav-link flex items-center px-3 py-2 rounded-md ${isActive('/result/') ? 'active text-white' : 'text-primary-100 hover:text-white'}`}
                                >
                                    <i className="fas fa-chart-line mr-2"></i>
                                    Analytics
                                    <i className={`fas fa-chevron-down ml-2 text-xs transition-transform duration-200 ${activeDropdown === 'analytics' ? 'rotate-180' : ''}`}></i>
                                </button>
                                <div className={`dropdown-content absolute left-0 mt-2 w-48 rounded-md shadow-lg bg-white z-50 ${activeDropdown === 'analytics' ? 'show' : ''}`}>
                                    <a
                                        href="/result/"
                                        className="block px-4 py-2 text-sm text-secondary-700 hover:bg-primary-50 hover:text-primary-700 rounded-md"
                                    >
                                        <i className="fas fa-chart-bar mr-2 text-primary-500"></i>
                                        View Statistics
                                    </a>
                                </div>
                            </div>

                            <div className="dropdown relative">
                                <button
                                    onClick={() => toggleDropdown('users')}
                                    className={`nav-link flex items-center px-3 py-2 rounded-md ${isActive('/manage_users/') ? 'active text-white' : 'text-primary-100 hover:text-white'}`}
                                >
                                    <i className="fas fa-users mr-2"></i>
                                    Users
                                    <i className={`fas fa-chevron-down ml-2 text-xs transition-transform duration-200 ${activeDropdown === 'users' ? 'rotate-180' : ''}`}></i>
                                </button>
                                <div className={`dropdown-content absolute left-0 mt-2 w-48 rounded-md shadow-lg bg-white z-50 ${activeDropdown === 'users' ? 'show' : ''}`}>
                                    <a
                                        href="/manage_users/"
                                        className="block px-4 py-2 text-sm text-secondary-700 hover:bg-primary-50 hover:text-primary-700 rounded-md"
                                    >
                                        <i className="fas fa-user-cog mr-2 text-primary-500"></i>
                                        Manage Users
                                    </a>
                                </div>
                            </div>
                        </nav>

                        {/* Right Side - User Menu */}
                        <div className="flex items-center">
                            <div className="dropdown relative">
                                <button
                                    onClick={() => toggleDropdown('user')}
                                    className="flex items-center space-x-2 px-3 py-2 rounded-md hover:bg-primary-600 transition-colors duration-200"
                                >
                                    <div className="bg-white/10 p-1.5 rounded-full">
                                        <i className="fas fa-user text-sm"></i>
                                    </div>
                                    <span className="hidden md:block">{{ user.username }}</span>
                                    <i className={`fas fa-chevron-down text-xs transition-transform duration-200 ${activeDropdown === 'user' ? 'rotate-180' : ''}`}></i>
                                </button>
                                <div className={`dropdown-content absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-white z-50 ${activeDropdown === 'user' ? 'show' : ''}`}>
                                    <a
                                        href="/admin_change_password/"
                                        className="block px-4 py-2 text-sm text-secondary-700 hover:bg-primary-50 hover:text-primary-700 rounded-t-md"
                                    >
                                        <i className="fas fa-key mr-2 text-primary-500"></i>
                                        Change Password
                                    </a>
                                    <a
                                        href="/logout/"
                                        className="block px-4 py-2 text-sm text-secondary-700 hover:bg-primary-50 hover:text-primary-700 rounded-b-md"
                                    >
                                        <i className="fas fa-sign-out-alt mr-2 text-primary-500"></i>
                                        Logout
                                    </a>
                                </div>
                            </div>

                            {/* Mobile Menu Button */}
                            <button
                                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                                className="md:hidden ml-2 p-2 rounded-md hover:bg-primary-600 transition-colors duration-200"
                            >
                                <i className={`fas ${mobileMenuOpen ? 'fa-times' : 'fa-bars'}`}></i>
                            </button>
                        </div>
                    </div>
                </div>

                {/* Mobile Menu */}
                <div className={`mobile-menu md:hidden ${mobileMenuOpen ? 'show' : ''}`}>
                    <div className="px-2 pt-2 pb-3 space-y-1">
                        <a
                            href="/admin_dashboard/"
                            className={`block px-3 py-2 rounded-md ${isActive('/admin_dashboard/') ? 'bg-primary-600 text-white' : 'text-primary-100 hover:bg-primary-600 hover:text-white'}`}
                        >
                            <i className="fas fa-home mr-2"></i>
                            Dashboard
                        </a>
                        <a
                            href="/upload/"
                            className={`block px-3 py-2 rounded-md ${isActive('/upload/') ? 'bg-primary-600 text-white' : 'text-primary-100 hover:bg-primary-600 hover:text-white'}`}
                        >
                            <i className="fas fa-upload mr-2"></i>
                            Upload Data
                        </a>
                        <a
                            href="/data_overview/"
                            className={`block px-3 py-2 rounded-md ${isActive('/data_overview/') ? 'bg-primary-600 text-white' : 'text-primary-100 hover:bg-primary-600 hover:text-white'}`}
                        >
                            <i className="fas fa-table mr-2"></i>
                            Data Overview
                        </a>
                        <a
                            href="/result/"
                            className={`block px-3 py-2 rounded-md ${isActive('/result/') ? 'bg-primary-600 text-white' : 'text-primary-100 hover:bg-primary-600 hover:text-white'}`}
                        >
                            <i className="fas fa-chart-bar mr-2"></i>
                            View Statistics
                        </a>
                        <a
                            href="/manage_users/"
                            className={`block px-3 py-2 rounded-md ${isActive('/manage_users/') ? 'bg-primary-600 text-white' : 'text-primary-100 hover:bg-primary-600 hover:text-white'}`}
                        >
                            <i className="fas fa-users mr-2"></i>
                            Manage Users
                        </a>
                        <a
                            href="/admin_change_password/"
                            className="block px-3 py-2 rounded-md text-primary-100 hover:bg-primary-600 hover:text-white"
                        >
                            <i className="fas fa-key mr-2"></i>
                            Change Password
                        </a>
                        <a
                            href="/logout/"
                            className="block px-3 py-2 rounded-md text-primary-100 hover:bg-primary-600 hover:text-white"
                        >
                            <i className="fas fa-sign-out-alt mr-2"></i>
                            Logout
                        </a>
                    </div>
                </div>
            </header>
        );
    };

    // Render the Navbar component
    const navbarContainer = document.getElementById('react-navbar');
    if (navbarContainer) {
        ReactDOM.render(<Navbar />, navbarContainer);
    }
}

// Dashboard Component
function renderDashboard() {
    // Dashboard Components
    const StatCard = ({ icon, title, value, trend, trendValue, trendDirection }) => {
        return (
            <div className="bg-white rounded-xl shadow-soft overflow-hidden transition-all duration-300 hover:shadow-lg group">
                <div className="p-6">
                    <div className="flex items-center justify-between mb-4">
                        <div className="bg-primary-50 text-primary-600 p-3 rounded-lg transition-all duration-300 group-hover:bg-primary-100 group-hover:text-primary-700">
                            <i className={`fas fa-${icon} text-xl`}></i>
                        </div>
                        <div className={`text-sm font-medium px-2 py-1 rounded-full ${trendDirection === 'up' ? 'bg-success-50 text-success-700' : 'bg-danger-50 text-danger-700'}`}>
                            <i className={`fas fa-arrow-${trendDirection} mr-1`}></i>
                            {trend}
                        </div>
                    </div>
                    <h3 className="text-3xl font-bold text-secondary-800">{value}</h3>
                    <p className="text-sm text-secondary-500 mt-1">{title}</p>
                    <div className="mt-4 pt-4 border-t border-secondary-100">
                        <p className="text-xs text-secondary-500">{trendValue}</p>
                    </div>
                </div>
            </div>
        );
    };

    const QuickAction = ({ icon, title, href, color }) => {
        return (
            <a
                href={href}
                className="flex items-center p-4 bg-white rounded-xl shadow-soft hover:shadow-md transition-all duration-300 transform hover:translate-x-1 group"
            >
                <div className={`${color} p-3 rounded-lg transition-all duration-300 group-hover:scale-110`}>
                    <i className={`fas fa-${icon} text-white`}></i>
                </div>
                <div className="ml-4">
                    <h3 className="font-medium text-secondary-800">{title}</h3>
                    <p className="text-xs text-secondary-500 mt-1">Click to access</p>
                </div>
                <div className="ml-auto">
                    <i className="fas fa-chevron-right text-secondary-400 group-hover:text-primary-500 transition-colors duration-300"></i>
                </div>
            </a>
        );
    };

    const TabButton = ({ id, label, icon, active, onClick }) => {
        return (
            <button
                onClick={() => onClick(id)}
                className={`flex items-center px-4 py-3 border-b-2 font-medium transition-all duration-200 ${
                    active
                        ? 'border-primary-500 text-primary-700'
                        : 'border-transparent text-secondary-500 hover:text-secondary-700 hover:border-secondary-300'
                }`}
            >
                <i className={`fas fa-${icon} mr-2 ${active ? 'text-primary-500' : 'text-secondary-400'}`}></i>
                {label}
            </button>
        );
    };

    const Dashboard = () => {
        const [activeTab, setActiveTab] = React.useState('overview');

        return (
            <div className="space-y-8">
                {/* Welcome Banner */}
                <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-xl shadow-soft text-white p-6">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
                        <div>
                            <h1 className="text-3xl font-bold mb-2">Welcome, {{ user.username }}</h1>
                            <p className="text-primary-100">Explore your dashboard and manage activities.</p>
                        </div>
                        <div className="mt-4 md:mt-0">
                            <button className="bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded-lg transition-all duration-300 flex items-center">
                                <i className="fas fa-cog mr-2"></i>
                                Settings
                            </button>
                        </div>
                    </div>
                </div>

                {/* Statistics Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <StatCard
                        icon="database"
                        title="Total Records"
                        value="{{ total_records }}"
                        trend="+12.5%"
                        trendValue="Compared to last month"
                        trendDirection="up"
                    />
                    <StatCard
                        icon="users"
                        title="Active Users"
                        value="{{ active_users }}"
                        trend="+2"
                        trendValue="New users this week"
                        trendDirection="up"
                    />
                    <StatCard
                        icon="map-marker-alt"
                        title="Unique Locations"
                        value="{{ unique_locations }}"
                        trend="+4"
                        trendValue="New locations added"
                        trendDirection="up"
                    />
                </div>

                {/* Tabs */}
                <div className="bg-white rounded-xl shadow-soft overflow-hidden">
                    <div className="flex border-b">
                        <TabButton
                            id="overview"
                            label="Overview"
                            icon="home"
                            active={activeTab === 'overview'}
                            onClick={setActiveTab}
                        />
                        <TabButton
                            id="analytics"
                            label="Analytics"
                            icon="chart-line"
                            active={activeTab === 'analytics'}
                            onClick={setActiveTab}
                        />
                        <TabButton
                            id="reports"
                            label="Reports"
                            icon="file-alt"
                            active={activeTab === 'reports'}
                            onClick={setActiveTab}
                        />
                    </div>

                    {/* Tab Content */}
                    <div className="p-6">
                        {activeTab === 'overview' && (
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                                {/* Recent Activity */}
                                <div className="lg:col-span-2">
                                    <div className="mb-4">
                                        <h2 className="text-xl font-semibold text-secondary-800">Recent Activity</h2>
                                        <p className="text-sm text-secondary-500">Your recent data processing activities</p>
                                    </div>
                                    <div className="bg-secondary-50 border border-secondary-200 rounded-xl p-6 min-h-[300px] flex items-center justify-center">
                                        <div className="text-center">
                                            <div className="text-primary-400 mb-4">
                                                <i className="fas fa-chart-line text-5xl animate-pulse-slow"></i>
                                            </div>
                                            <p className="text-secondary-400">Activity chart will appear here</p>
                                            <button className="mt-4 px-4 py-2 bg-primary-50 text-primary-600 rounded-lg hover:bg-primary-100 transition-colors duration-200">
                                                <i className="fas fa-sync-alt mr-2"></i>
                                                Refresh Data
                                            </button>
                                        </div>
                                    </div>
                                </div>

                                {/* Quick Actions */}
                                <div>
                                    <div className="mb-4">
                                        <h2 className="text-xl font-semibold text-secondary-800">Quick Actions</h2>
                                        <p className="text-sm text-secondary-500">Essential operations</p>
                                    </div>

                                    <div className="space-y-3">
                                        <QuickAction
                                            icon="upload"
                                            title="Upload Data"
                                            href="/upload/"
                                            color="bg-primary-600"
                                        />
                                        <QuickAction
                                            icon="file-alt"
                                            title="Generate Report"
                                            href="#"
                                            color="bg-success-500"
                                        />
                                        <QuickAction
                                            icon="key"
                                            title="Change Password"
                                            href="/admin_change_password/"
                                            color="bg-warning-500"
                                        />
                                        <QuickAction
                                            icon="exclamation-triangle"
                                            title="Report Issue"
                                            href="#"
                                            color="bg-danger-500"
                                        />
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === 'analytics' && (
                            <div className="text-center py-12">
                                <i className="fas fa-chart-pie text-5xl text-secondary-300 mb-4"></i>
                                <h3 className="text-xl font-medium text-secondary-700">Analytics Content</h3>
                                <p className="text-secondary-500 mt-2">Analytics content will appear here</p>
                                <a
                                    href="/result/"
                                    className="inline-block mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors duration-200"
                                >
                 transition-colors duration-200">
                                    <i className="fas fa-chart-bar mr-2"></i>
                                    View Statistics
                                </a>
                            </div>
                        )}

                        {activeTab === 'reports' && (
                            <div className="text-center py-12">
                                <i className="fas fa-file-alt text-5xl text-secondary-300 mb-4"></i>
                                <h3 className="text-xl font-medium text-secondary-700">Reports Content</h3>
                                <p className="text-secondary-500 mt-2">Reports content will appear here</p>
                                <button
                                    className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors duration-200"
                                >
                                    <i className="fas fa-download mr-2"></i>
                                    Generate Report
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                {/* System Status */}
                <div className="bg-white rounded-xl shadow-soft p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-xl font-semibold text-secondary-800">System Status</h2>
                        <span className="px-3 py-1 bg-success-50 text-success-700 rounded-full text-sm">
                            <i className="fas fa-check-circle mr-1"></i> All Systems Operational
                        </span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-secondary-50 rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-secondary-700">Database</span>
                                <span className="text-success-500"><i className="fas fa-circle text-xs"></i></span>
                            </div>
                            <div className="h-2 bg-secondary-200 rounded-full overflow-hidden">
                                <div className="h-full bg-primary-500 rounded-full" style={{width: '65%'}}></div>
                            </div>
                            <p className="text-xs text-secondary-500 mt-2">65% capacity</p>
                        </div>
                        <div className="bg-secondary-50 rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-secondary-700">API</span>
                                <span className="text-success-500"><i className="fas fa-circle text-xs"></i></span>
                            </div>
                            <div className="h-2 bg-secondary-200 rounded-full overflow-hidden">
                                <div className="h-full bg-primary-500 rounded-full" style={{width: '23%'}}></div>
                            </div>
                            <p className="text-xs text-secondary-500 mt-2">23% usage</p>
                        </div>
                        <div className="bg-secondary-50 rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-secondary-700">Storage</span>
                                <span className="text-success-500"><i className="fas fa-circle text-xs"></i></span>
                            </div>
                            <div className="h-2 bg-secondary-200 rounded-full overflow-hidden">
                                <div className="h-full bg-primary-500 rounded-full" style={{width: '42%'}}></div>
                            </div>
                            <p className="text-xs text-secondary-500 mt-2">42% used</p>
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    // Render the Dashboard component
    const dashboardContainer = document.getElementById('react-dashboard');
    if (dashboardContainer) {
        ReactDOM.render(<Dashboard />, dashboardContainer);
    }
}

// Additional utility functions
function formatDate(date) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(date).toLocaleDateString(undefined, options);
}

function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}