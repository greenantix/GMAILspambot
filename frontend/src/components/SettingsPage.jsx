import React, { useState, useEffect } from 'react';
import { apiService, handleApiError } from '../services/api';
import Card from './shared/Card';
import Button from './shared/Button';
import Icon from './shared/Icon';

const SettingsPage = () => {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [activeTab, setActiveTab] = useState('general');
  const [lmStudioLoading, setLmStudioLoading] = useState(false);
  const [lmStudioStatus, setLmStudioStatus] = useState(null);
  const [lmStudioModels, setLmStudioModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');

  useEffect(() => {
    loadSettings();
    fetchLmStudioStatus();
    fetchLmStudioModels();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const response = await apiService.get('/settings');
      setSettings(response.data);
      setError(null);
    } catch (err) {
      setError(handleApiError(err, 'Failed to load settings'));
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    try {
      setSaving(true);
      await apiService.put('/settings', settings);
      setSuccess('Settings saved successfully');
      setError(null);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(handleApiError(err, 'Failed to save settings'));
    } finally {
      setSaving(false);
    }
  };

  const exportSettings = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/settings/export');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `gmail_bot_settings_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError('Failed to export settings');
    }
  };

  const importSettings = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    fetch('http://localhost:5000/api/settings/import', {
      method: 'POST',
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        setError(data.error);
      } else {
        setSuccess('Settings imported successfully');
        loadSettings();
      }
    })
    .catch(err => {
      setError('Failed to import settings');
    });

    event.target.value = '';
  };

  const fetchLmStudioStatus = async () => {
    try {
      const response = await apiService.get('/lmstudio/status');
      setLmStudioStatus(response.data);
    } catch (err) {
      setLmStudioStatus({ status: 'not_running' });
    }
  };

  const fetchLmStudioModels = async () => {
    try {
      const response = await apiService.get('/lmstudio/models');
      setLmStudioModels(response.data);
      // Set default model if not already set
      if (!selectedModel && response.data.medium) {
        setSelectedModel('medium');
      }
    } catch (err) {
      setError('Failed to fetch LM Studio models');
    }
  };

  const runLmStudioAnalysis = async () => {
    try {
      setLmStudioLoading(true);
      const response = await apiService.post('/lmstudio/analyze', {
        use_existing_export: true
      });
      
      setSuccess('LM Studio analysis completed successfully');
      // Optionally, you can handle the results here
      
    } catch (err) {
      setError(handleApiError(err, 'LM Studio analysis failed'));
    } finally {
      setLmStudioLoading(false);
    }
  };

  const switchLmStudioModel = async (modelKey) => {
    try {
      await apiService.post('/lmstudio/switch-model', { model_key: modelKey });
      setSelectedModel(modelKey);
      fetchLmStudioStatus(); // Refresh status after switching
      setSuccess(`Switched to ${modelKey} model`);
    } catch (err) {
      setError(`Failed to switch to ${modelKey} model`);
    }
  };

  const updateSetting = (path, value) => {
    const pathArray = path.split('.');
    const newSettings = { ...settings };
    let current = newSettings;
    
    for (let i = 0; i < pathArray.length - 1; i++) {
      if (!current[pathArray[i]]) current[pathArray[i]] = {};
      current = current[pathArray[i]];
    }
    
    current[pathArray[pathArray.length - 1]] = value;
    setSettings(newSettings);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Icon name="loader" className="animate-spin text-blue-500" size={32} />
        <span className="ml-2 text-gray-300">Loading settings...</span>
      </div>
    );
  }

  if (!settings) {
    return (
      <Card className="text-center py-8">
        <Icon name="settings" className="mx-auto mb-4 text-gray-400" size={48} />
        <h3 className="text-lg font-medium text-white mb-2">Settings Not Found</h3>
        <p className="text-gray-300">Unable to load system settings.</p>
      </Card>
    );
  }

  const tabs = [
    { id: 'general', name: 'General', icon: 'settings' },
    { id: 'ai', name: 'AI & LLM', icon: 'brain' },
    { id: 'gmail', name: 'Gmail', icon: 'mail' },
    { id: 'cleanup', name: 'Cleanup', icon: 'trash' },
    { id: 'advanced', name: 'Advanced', icon: 'code' }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Settings</h1>
          <p className="text-gray-300 mt-1">
            Configure Gmail Spam Bot behavior and preferences
          </p>
        </div>
        <div className="flex space-x-3">
          <Button variant="outline" onClick={exportSettings}>
            <Icon name="download" className="mr-2" />
            Export
          </Button>
          <label className="cursor-pointer">
            <Button variant="outline">
              <Icon name="upload" className="mr-2" />
              Import
            </Button>
            <input
              type="file"
              accept=".json"
              onChange={importSettings}
              className="hidden"
            />
          </label>
          <Button onClick={saveSettings} disabled={saving}>
            {saving ? (
              <>
                <Icon name="loader" className="animate-spin mr-2" />
                Saving...
              </>
            ) : (
              <>
                <Icon name="save" className="mr-2" />
                Save Settings
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Messages */}
      {error && (
        <Card className="border-red-500 bg-red-900/20">
          <div className="flex items-center">
            <Icon name="alertCircle" className="text-red-400 mr-2" />
            <span className="text-red-300">{error}</span>
            <Button 
              variant="ghost" 
              size="sm" 
              className="ml-auto text-red-300"
              onClick={() => setError(null)}
            >
              <Icon name="x" />
            </Button>
          </div>
        </Card>
      )}

      {success && (
        <Card className="border-green-500 bg-green-900/20">
          <div className="flex items-center">
            <Icon name="checkCircle" className="text-green-400 mr-2" />
            <span className="text-green-300">{success}</span>
            <Button 
              variant="ghost" 
              size="sm" 
              className="ml-auto text-green-300"
              onClick={() => setSuccess(null)}
            >
              <Icon name="x" />
            </Button>
          </div>
        </Card>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-600">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center ${
                activeTab === tab.id
                  ? 'border-blue-400 text-blue-400'
                  : 'border-transparent text-gray-400 hover:text-gray-200'
              }`}
            >
              <Icon name={tab.icon} className="mr-2" size={16} />
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="space-y-6">
        {activeTab === 'general' && (
          <GeneralSettings settings={settings} updateSetting={updateSetting} />
        )}
        
        {activeTab === 'ai' && (
          <LMStudioSettings
            settings={settings}
            updateSetting={updateSetting}
            runAnalysis={runLmStudioAnalysis}
            loading={lmStudioLoading}
            status={lmStudioStatus}
            models={lmStudioModels}
            selectedModel={selectedModel}
            switchModel={switchLmStudioModel}
          />
        )}
        
        {activeTab === 'gmail' && (
          <GmailSettings settings={settings} updateSetting={updateSetting} />
        )}
        
        {activeTab === 'cleanup' && (
          <CleanupSettings settings={settings} updateSetting={updateSetting} />
        )}
        
        {activeTab === 'advanced' && (
          <AdvancedSettings settings={settings} updateSetting={updateSetting} />
        )}
      </div>
    </div>
  );
};

const GeneralSettings = ({ settings, updateSetting }) => (
  <Card>
    <h3 className="text-lg font-semibold text-white mb-4">General Settings</h3>
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Log Level
        </label>
        <select
          value={settings.logging?.level || 'INFO'}
          onChange={(e) => updateSetting('logging.level', e.target.value)}
          className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white"
        >
          <option value="DEBUG">Debug</option>
          <option value="INFO">Info</option>
          <option value="WARNING">Warning</option>
          <option value="ERROR">Error</option>
        </select>
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Max Emails Per Batch
        </label>
        <input
          type="number"
          value={settings.processing?.batch_size || 100}
          onChange={(e) => updateSetting('processing.batch_size', parseInt(e.target.value))}
          className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white"
          min="1"
          max="1000"
        />
      </div>
    </div>
  </Card>
);

const LMStudioSettings = ({
  settings,
  updateSetting,
  runAnalysis,
  loading,
  status,
  models,
  selectedModel,
  switchModel,
}) => (
  <div className="space-y-6">
    <Card>
      <h3 className="text-lg font-semibold text-white mb-4">LM Studio Control</h3>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-gray-300">Server Status:</span>
          {status ? (
            <div className={`flex items-center px-2 py-1 rounded-full text-xs font-medium ${
              status.status === 'running' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'
            }`}>
              <Icon name={status.status === 'running' ? 'checkCircle' : 'alertCircle'} className="mr-1" size={14} />
              {status.status === 'running' ? `Running (Model: ${status.loaded_model || 'Unknown'})` : 'Not Running'}
            </div>
          ) : (
            <span className="text-gray-400">Loading...</span>
          )}
        </div>
const ModelPerformanceMetrics = () => (
  <Card>
    <h3 className="text-lg font-semibold text-white mb-4">Model Performance</h3>
    <div className="space-y-2 text-sm text-gray-300">
      <div className="flex justify-between">
        <span>Response Time:</span>
        <span className="font-medium text-white">N/A</span>
      </div>
      <div className="flex justify-between">
        <span>Tokens per Second:</span>
        <span className="font-medium text-white">N/A</span>
      </div>
      <div className="flex justify-between">
        <span>Last Analysis Duration:</span>
        <span className="font-medium text-white">N/A</span>
      </div>
    </div>
  </Card>
);

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Active Model
          </label>
          <select
            value={selectedModel}
            onChange={(e) => switchModel(e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white"
            disabled={!status || status.status !== 'running'}
          >
            {Object.entries(models).map(([key, model]) => (
              <option key={key} value={key}>
                {model.name} ({key})
              </option>
            ))}
          </select>
        </div>

        <Button
          onClick={runAnalysis}
          disabled={loading || !status || status.status !== 'running'}
          className="w-full"
        >
          {loading ? (
            <>
              <Icon name="loader" className="animate-spin mr-2" />
              Running Analysis...
            </>
          ) : (
            <>
              <Icon name="brain" className="mr-2" />
              Run LM Studio Analysis
            </>
          )}
        </Button>
      </div>
    </Card>

    <Card>
      <h3 className="text-lg font-semibold text-white mb-4">LLM Configuration</h3>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            LM Studio Endpoint
          </label>
          <input
            type="url"
            value={settings.lm_studio?.endpoint || 'http://localhost:1234/v1'}
            onChange={(e) => updateSetting('lm_studio.endpoint', e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white"
            placeholder="http://localhost:1234/v1"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Temperature
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={settings.lm_studio?.temperature || 0.3}
            onChange={(e) => updateSetting('lm_studio.temperature', parseFloat(e.target.value))}
            className="w-full"
          />
          <span className="text-sm text-gray-400">
            {settings.lm_studio?.temperature || 0.3}
          </span>
        </div>
      </div>
    </Card>
  </div>
);

const GmailSettings = ({ settings, updateSetting }) => (
  <Card>
    <h3 className="text-lg font-semibold text-white mb-4">Gmail Configuration</h3>
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Enable Server-Side Filtering
        </label>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={settings.gmail?.use_server_side_filtering || false}
            onChange={(e) => updateSetting('gmail.use_server_side_filtering', e.target.checked)}
            className="rounded border-gray-600 bg-gray-700 text-blue-500"
          />
          <span className="ml-2 text-gray-300">Use Gmail's server-side filters before LLM processing</span>
        </label>
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          API Request Delay (ms)
        </label>
        <input
          type="number"
          value={settings.gmail?.request_delay || 100}
          onChange={(e) => updateSetting('gmail.request_delay', parseInt(e.target.value))}
          className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white"
          min="0"
          max="5000"
        />
      </div>
    </div>
  </Card>
);

const CleanupSettings = ({ settings, updateSetting }) => (
  <Card>
    <h3 className="text-lg font-semibold text-white mb-4">Email Cleanup Settings</h3>
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Auto-cleanup JUNK emails after (days)
        </label>
        <input
          type="number"
          value={settings.cleanup?.junk_retention_days || 30}
          onChange={(e) => updateSetting('cleanup.junk_retention_days', parseInt(e.target.value))}
          className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white"
          min="1"
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Auto-cleanup NEWSLETTERS emails after (days)
        </label>
        <input
          type="number"
          value={settings.cleanup?.newsletter_retention_days || 90}
          onChange={(e) => updateSetting('cleanup.newsletter_retention_days', parseInt(e.target.value))}
          className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white"
          min="1"
        />
      </div>
    </div>
  </Card>
);

const AdvancedSettings = ({ settings, updateSetting }) => (
  <Card>
    <h3 className="text-lg font-semibold text-white mb-4">Advanced Settings</h3>
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Enable Debug Mode
        </label>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={settings.debug?.enabled || false}
            onChange={(e) => updateSetting('debug.enabled', e.target.checked)}
            className="rounded border-gray-600 bg-gray-700 text-blue-500"
          />
          <span className="ml-2 text-gray-300">Enable detailed debugging output</span>
        </label>
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Backup Settings Automatically
        </label>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={settings.backup?.auto_backup || true}
            onChange={(e) => updateSetting('backup.auto_backup', e.target.checked)}
            className="rounded border-gray-600 bg-gray-700 text-blue-500"
          />
          <span className="ml-2 text-gray-300">Automatically backup settings before changes</span>
        </label>
      </div>
    </div>
  </Card>
);

export default SettingsPage;