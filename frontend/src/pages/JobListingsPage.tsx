import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { 
  Search, 
  Filter, 
  MapPin, 
  Clock, 
  Heart, 
  ExternalLink,
  Briefcase,
  TrendingUp,
  Users,
  DollarSign,
  RefreshCw
} from 'lucide-react';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Card from '../components/ui/Card';
import { buildJobForgeUrl } from '../config/api';

interface Job {
  id: number;
  title: string;
  company: string;
  apply_link: string;
  description: string;
  publish_date: string;
  locations: string[];
  skills: string[];
  education: string[];
  relevance: number;
}

const JobListingsPage: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [filteredJobs, setFilteredJobs] = useState<Job[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFilters, setSelectedFilters] = useState({
    location: '',
    skills: [] as string[],
    minRelevance: 40,
  });
  const [showFilters, setShowFilters] = useState(false);
  const [sortBy, setSortBy] = useState('relevance');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTriggered, setSearchTriggered] = useState(false);

  // Load jobs from API
  useEffect(() => {
    const loadJobs = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const userId = localStorage.getItem('user_id') || 'x';
        console.log('Loading jobs for user:', userId); // Debug log
        
        const response = await axios.get(buildJobForgeUrl(`/recommend/${userId}`), {
          headers: {
            'Content-Type': 'application/json',
          },
        });
        
        console.log('Initial load response:', response.data); // Debug log
        
        if (response.data.results) {
          setJobs(response.data.results);
          setFilteredJobs(response.data.results);
        } else {
          throw new Error('Invalid response format');
        }
      } catch (error) {
        console.error('Error loading jobs:', error);
        if (axios.isAxiosError(error)) {
          console.error('Error details:', error.response?.data);
          console.error('Error status:', error.response?.status);
          console.error('Error headers:', error.response?.headers);
          setError(`Failed to load jobs: ${error.response?.data?.detail || error.message}`);
        } else {
          setError('Failed to load jobs. Please try again.');
        }
        // Fallback to empty array
        setJobs([]);
        setFilteredJobs([]);
      } finally {
        setLoading(false);
      }
    };

    loadJobs();
  }, []);

  // Apply filters when sortBy changes
  useEffect(() => {
    filterJobs(searchTerm, selectedFilters);
  }, [sortBy]);

  const jobTypes = ['Full-time', 'Part-time', 'Contract', 'Internship'];
  const locations = ['Remote', 'San Francisco, CA', 'New York, NY', 'Mountain View, CA', 'Austin, TX'];
  const salaryRanges = ['$50k+', '$100k+', '$150k+', '$200k+'];

  // Search function that only triggers on button click
  const handleSearchClick = () => {
    setSearchTriggered(true);
    handleSearch(searchTerm);
  };

  const handleSearch = async (term: string) => {
    setSearchTerm(term);
    
    if (term.trim()) {
      try {
        setLoading(true);
        setError(null);
        
        const userId = localStorage.getItem('user_id') || 'x';
        const payload = {
          titles: [term],
          top_k: 20,
          min_relevance: selectedFilters.minRelevance
        };
        
        console.log('Searching with payload:', payload); // Debug log
        console.log('Search URL:', buildJobForgeUrl(`/search/${userId}`)); // Debug log
        
        const response = await axios.post(buildJobForgeUrl(`/search/${userId}`), payload, {
          headers: {
            'Content-Type': 'application/json',
          },
        });
        
        console.log('Search response:', response.data); // Debug log
        
        if (response.data.results) {
          setJobs(response.data.results);
          setFilteredJobs(response.data.results);
        } else {
          throw new Error('Invalid response format');
        }
      } catch (error) {
        console.error('Error searching jobs:', error);
        if (axios.isAxiosError(error)) {
          console.error('Error details:', error.response?.data);
          console.error('Error status:', error.response?.status);
          console.error('Error headers:', error.response?.headers);
          setError(`Failed to search jobs: ${error.response?.data?.detail || error.message}`);
        } else {
          setError('Failed to search jobs. Please try again.');
        }
      } finally {
        setLoading(false);
      }
    } else {
      // If search term is empty, reload recommended jobs
      const loadJobs = async () => {
        try {
          setLoading(true);
          setError(null);
          
          const userId = localStorage.getItem('user_id') || 'x';
          console.log('Loading recommendations for user:', userId); // Debug log
          
          const response = await axios.get(buildJobForgeUrl(`/recommend/${userId}`), {
            headers: {
              'Content-Type': 'application/json',
            },
          });
          
          console.log('Recommend response:', response.data); // Debug log
          
          if (response.data.results) {
            setJobs(response.data.results);
            setFilteredJobs(response.data.results);
          } else {
            throw new Error('Invalid response format');
          }
        } catch (error) {
          console.error('Error loading jobs:', error);
          if (axios.isAxiosError(error)) {
            console.error('Error details:', error.response?.data);
            console.error('Error status:', error.response?.status);
            console.error('Error headers:', error.response?.headers);
            setError(`Failed to load jobs: ${error.response?.data?.detail || error.message}`);
          } else {
            setError('Failed to load jobs. Please try again.');
          }
        } finally {
          setLoading(false);
        }
      };
      
      loadJobs();
    }
  };

  const handleFilterChange = (key: string, value: string | string[] | number) => {
    const newFilters = { ...selectedFilters, [key]: value };
    setSelectedFilters(newFilters);
    // Don't auto-apply filters, wait for refresh button
  };

  const handleRefreshWithFilters = async () => {
    if (searchTriggered && searchTerm.trim()) {
      // Re-run search with new filters
      await handleSearch(searchTerm);
    } else {
      // Re-run recommendations with new filters
      const loadJobs = async () => {
        try {
          setLoading(true);
          setError(null);
          
          const userId = localStorage.getItem('user_id') || 'x';
          const response = await axios.get(buildJobForgeUrl(`/recommend/${userId}`), {
            headers: {
              'Content-Type': 'application/json',
            },
          });
          
          if (response.data.results) {
            setJobs(response.data.results);
            // Apply filters immediately after loading
            filterJobs(searchTerm, selectedFilters);
          } else {
            throw new Error('Invalid response format');
          }
        } catch (error) {
          console.error('Error loading jobs:', error);
          setError('Failed to load jobs. Please try again.');
        } finally {
          setLoading(false);
        }
      };
      
      loadJobs();
    }
  };

  const filterJobs = (search: string, filters: typeof selectedFilters) => {
    console.log('Filtering jobs with:', { search, filters, sortBy });
    
    let filtered = jobs.filter(job => {
      const matchesSearch = search === '' || job.title.toLowerCase().includes(search.toLowerCase()) ||
                          job.company.toLowerCase().includes(search.toLowerCase()) ||
                          job.skills.some(skill => skill.toLowerCase().includes(search.toLowerCase()));
      
      const matchesLocation = !filters.location || 
                             job.locations.some(location => location.toLowerCase().includes(filters.location.toLowerCase()));
      const matchesSkills = filters.skills.length === 0 || 
                           filters.skills.some(skill => job.skills.includes(skill));
      const matchesRelevance = job.relevance >= filters.minRelevance;

      return matchesSearch && matchesLocation && matchesSkills && matchesRelevance;
    });

    // Sort jobs
    switch (sortBy) {
      case 'relevance':
        filtered.sort((a, b) => b.relevance - a.relevance);
        break;
      case 'date':
        filtered.sort((a, b) => new Date(b.publish_date).getTime() - new Date(a.publish_date).getTime());
        break;
    }

    console.log('Filtered jobs count:', filtered.length);
    setFilteredJobs(filtered);
  };

  const getMatchColor = (score: number) => {
    if (score >= 90) return 'text-green-400';
    if (score >= 80) return 'text-yellow-400';
    if (score >= 70) return 'text-orange-400';
    return 'text-red-400';
  };

  const getMatchBg = (score: number) => {
    if (score >= 90) return 'bg-green-500/20';
    if (score >= 80) return 'bg-yellow-500/20';
    if (score >= 70) return 'bg-orange-500/20';
    return 'bg-red-500/20';
  };

  if (loading) {
    return (
      <div className="min-h-screen pt-16 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-white/20 border-t-blue-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-white/70">Loading jobs...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-36 pb-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-4">
            Find Your <span className="gradient-text">Dream Job</span>
          </h1>
          <p className="text-xl text-white/70">
            Discover opportunities that match your skills and aspirations
          </p>
        </div>

        {/* Search and Filters */}
        <div className="mb-8">
          <div className="flex flex-col lg:flex-row gap-4 mb-6">
            <div className="flex-1">
              <div className="flex gap-2 text-black">
                <Input
                  placeholder={loading ? "Searching..." : "Search jobs, companies, or skills..."}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  icon={<Search size={20} />}
                  disabled={loading}
                />
                <Button
                  onClick={handleSearchClick}
                  loading={loading}
                  icon={<Search size={20} />}
                >
                  Search
                </Button>
                {searchTerm && (
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setSearchTerm('');
                      setSearchTriggered(false);
                      handleSearch('');
                    }}
                  >
                    Clear
                  </Button>
                )}
              </div>
            </div>
            <Button
              variant="glass"
              onClick={() => setShowFilters(!showFilters)}
              icon={<Filter size={20} />}
            >
              Filters
            </Button>
          </div>

          {/* Filter Panel */}
          <AnimatePresence>
            {showFilters && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mb-6"
              >
                <Card variant="glass" className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-white/90 mb-2">
                        Location
                      </label>
                      <select
                        value={selectedFilters.location}
                        onChange={(e) => handleFilterChange('location', e.target.value)}
                        className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-blue-400"
                      >
                        <option value="">All Locations</option>
                        {locations.map(location => (
                          <option key={location} value={location}>{location}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-white/90 mb-2">
                        Min Relevance (%)
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        value={selectedFilters.minRelevance}
                        onChange={(e) => handleFilterChange('minRelevance', parseInt(e.target.value) || 0)}
                        className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-blue-400"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-white/90 mb-2">
                        Sort By
                      </label>
                      <select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value)}
                        className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-blue-400"
                      >
                        <option value="relevance">Relevance</option>
                        <option value="date">Date Posted</option>
                      </select>
                    </div>
                  </div>
                  
                  <div className="mt-4 flex justify-end">
                    <Button
                      onClick={handleRefreshWithFilters}
                      loading={loading}
                      icon={<RefreshCw size={20} />}
                      variant="glass"
                    >
                      Apply Filters
                    </Button>
                  </div>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/20 border border-red-500/30 rounded-lg">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        {/* Results Count */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <p className="text-white/70">
              {filteredJobs.length} job{filteredJobs.length !== 1 ? 's' : ''} found
            </p>
            {searchTerm ? (
              <p className="text-blue-400 text-sm">
                Showing search results for "{searchTerm}"
              </p>
            ) : (
              <p className="text-green-400 text-sm">
                Showing personalized recommendations
              </p>
            )}
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-white/70">
              <TrendingUp size={16} />
              <span>High Match</span>
            </div>
            <div className="flex items-center space-x-2 text-white/70">
              <Users size={16} />
              <span>Popular</span>
            </div>
          </div>
        </div>

        {/* Job Listings */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Job Cards */}
          <div className="lg:col-span-2 space-y-4">
            <AnimatePresence>
              {filteredJobs.map((job, index) => (
                <motion.div
                  key={job.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                >
                  <Card variant="glass" className="p-6 hover:scale-[1.02] transition-all duration-300">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h3 className="text-xl font-semibold text-white">
                            {job.title}
                          </h3>
                          <div className={`px-2 py-1 rounded-full text-xs font-medium ${getMatchBg(job.relevance)} ${getMatchColor(job.relevance)}`}>
                            {job.relevance}% match
                          </div>
                        </div>
                        <p className="text-white/70 text-lg mb-2">
                          {job.company}
                        </p>
                        <div className="flex items-center space-x-4 text-white/60 text-sm">
                          <div className="flex items-center space-x-1">
                            <MapPin size={16} />
                            <span>{job.locations.join(', ')}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <Clock size={16} />
                            <span>{new Date(job.publish_date).toLocaleDateString()}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <p className="text-white/80 mb-4 line-clamp-2" dangerouslySetInnerHTML={{ __html: job.description }} />

                    <div className="flex flex-wrap gap-2 mb-4">
                      {job.skills.slice(0, 4).map((skill) => (
                        <span
                          key={skill}
                          className="px-3 py-1 bg-white/10 text-white/70 text-sm rounded-lg"
                        >
                          {skill}
                        </span>
                      ))}
                      {job.skills.length > 4 && (
                        <span className="px-3 py-1 bg-white/10 text-white/70 text-sm rounded-lg">
                          +{job.skills.length - 4} more
                        </span>
                      )}
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        {job.education.length > 0 && (
                          <div className="flex items-center space-x-1 text-blue-400">
                            <span className="font-medium">{job.education.join(', ')}</span>
                          </div>
                        )}
                      </div>
                      <div className="flex items-center space-x-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => window.open(job.apply_link, '_blank')}
                          icon={<ExternalLink size={16} />}
                        >
                          Apply
                        </Button>
                      </div>
                    </div>
                  </Card>
                </motion.div>
              ))}
            </AnimatePresence>

            {filteredJobs.length === 0 && (
              <Card variant="glass" className="p-12 text-center">
                <div className="w-16 h-16 bg-white/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <Search size={32} className="text-white/50" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">
                  No jobs found
                </h3>
                <p className="text-white/70">
                  Try adjusting your search criteria or filters
                </p>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Stats
            <Card variant="glass" className="p-6">
              <h3 className="text-lg font-semibold text-white mb-4">
                Your Job Search
              </h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-white/70">Jobs Applied</span>
                  <span className="text-white font-semibold">12</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-white/70">Interviews</span>
                  <span className="text-white font-semibold">3</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-white/70">Saved Jobs</span>
                  <span className="text-white font-semibold">0</span>
                </div>
              </div>
            </Card> */}

            {/* Top Skills */}
            <Card variant="glass" className="p-6">
              <h3 className="text-lg font-semibold text-white mb-4">
                Trending Skills
              </h3>
              <div className="space-y-2">
                {['React', 'Python', 'Machine Learning', 'AWS', 'TypeScript'].map((skill, index) => (
                  <div key={skill} className="flex items-center justify-between">
                    <span className="text-white/70">{skill}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-16 h-2 bg-white/10 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-gradient-to-r from-horizon-800 to-horizon-900 rounded-full"
                          style={{ width: `${90 - index * 10}%` }}
                        />
                      </div>
                      <span className="text-white/50 text-sm">{90 - index * 10}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Job Alerts */}
            <Card variant="glass" className="p-6">
              <h3 className="text-lg font-semibold text-white mb-4">
                Job Alerts
              </h3>
              <p className="text-white/70 text-sm mb-4">
                Get notified when new jobs match your criteria
              </p>
              <Button variant="glass" className="w-full">
                Create Alert
              </Button>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default JobListingsPage;
