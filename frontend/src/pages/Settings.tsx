import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { ChevronLeft, Search, Trash2, Save, X, FileText } from "lucide-react";
import { useTheme } from "@/contexts/ThemeContext";

const API_BASE = "";

interface EnvEntry {
  key: string | null;
  value: string;
  isCommentOrEmpty: boolean;
  isMultilineQuoted: boolean;
  originalLineNumStart: number;
  originalLineNumEnd: number;
}

interface Plugin {
  name: string;
  manifest: {
    displayName?: string;
    name: string;
    description?: string;
    version?: string;
    capabilities?: {
      invocationCommands?: Array<{
        commandIdentifier: string;
        command: string;
        description: string;
      }>;
    };
  };
  enabled: boolean;
  configEnvContent?: string;
}

interface DailyNote {
  name: string;
  folderName: string;
  lastModified: string;
  preview: string;
}

interface ApiResponse<T> {
  content?: T;
  message?: string;
  error?: string;
}

type NavSection = 'base-config' | 'daily-notes-manager' | string;

export function Settings() {
  const { theme } = useTheme();
  // Navigation state
  const [activeSection, setActiveSection] = useState<NavSection>('base-config');
  const [activePlugin, setActivePlugin] = useState<string | null>(null);

  // Base config state
  const [baseConfigEntries, setBaseConfigEntries] = useState<EnvEntry[]>([]);
  const [baseConfigLoading, setBaseConfigLoading] = useState(true);
  const [baseConfigStatus, setBaseConfigStatus] = useState("");

  // Plugins state
  const [plugins, setPlugins] = useState<Plugin[]>([]);

  // Plugin config state
  const [pluginConfigEntries, setPluginConfigEntries] = useState<Record<string, EnvEntry[]>>({});
  const [pluginEditingCommandDescriptions, setPluginEditingCommandDescriptions] = useState<Record<string, Record<string, string>>>({});

  // Daily notes state
  const [noteFolders, setNoteFolders] = useState<string[]>([]);
  const [activeFolder, setActiveFolder] = useState<string>("");
  const [notes, setNotes] = useState<DailyNote[]>([]);
  const [selectedNotes, setSelectedNotes] = useState<Set<string>>(new Set());
  const [editingNote, setEditingNote] = useState<DailyNote | null>(null);
  const [noteContent, setNoteContent] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [notesStatus, setNotesStatus] = useState("");

  // Message state
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' | 'info' } | null>(null);

  // Load initial data
  useEffect(() => {
    loadBaseConfig();
    loadPlugins();
    loadNoteFolders();
  }, []);

  // Load notes when folder changes
  useEffect(() => {
    if (activeFolder) {
      loadNotes(activeFolder);
    }
  }, [activeFolder]);

  // Show message helper
  const showMessage = (text: string, type: 'success' | 'error' | 'info' = 'info') => {
    setMessage({ text, type });
    setTimeout(() => setMessage(null), 3500);
  };

  // API helper
  const apiFetch = async (url: string, options?: RequestInit) => {
    const response = await fetch(url, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options?.headers },
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
      throw new Error(error.message || error.error || `HTTP ${response.status}`);
    }
    return response.json();
  };

  // Parse .env content to entries
  const parseEnvToList = (content: string): EnvEntry[] => {
    const lines = content.split(/\r?\n/);
    const entries: EnvEntry[] = [];
    let i = 0;

    while (i < lines.length) {
      const line = lines[i];
      const trimmedLine = line.trim();
      const currentLineNum = i;

      if (trimmedLine.startsWith('#') || trimmedLine === '') {
        entries.push({
          key: null,
          value: line,
          isCommentOrEmpty: true,
          isMultilineQuoted: false,
          originalLineNumStart: currentLineNum,
          originalLineNumEnd: currentLineNum
        });
        i++;
        continue;
      }

      const eqIndex = line.indexOf('=');
      if (eqIndex === -1) {
        entries.push({
          key: null,
          value: line,
          isCommentOrEmpty: true,
          isMultilineQuoted: false,
          originalLineNumStart: currentLineNum,
          originalLineNumEnd: currentLineNum
        });
        i++;
        continue;
      }

      const key = line.substring(0, eqIndex).trim();
      let valueString = line.substring(eqIndex + 1);

      if (valueString.trim().startsWith("'")) {
        let accumulatedValue: string;
        let firstLineContent = valueString.substring(valueString.indexOf("'") + 1);

        if (firstLineContent.endsWith("'") && !lines.slice(i + 1).some(l => l.trim().endsWith("'") && !l.trim().startsWith("'") && l.includes("='"))) {
          accumulatedValue = firstLineContent.substring(0, firstLineContent.length - 1);
          entries.push({
            key,
            value: accumulatedValue,
            isCommentOrEmpty: false,
            isMultilineQuoted: true,
            originalLineNumStart: currentLineNum,
            originalLineNumEnd: i
          });
        } else {
          let multilineContent = [firstLineContent];
          let endLineNum = i;
          i++;
          while (i < lines.length) {
            const nextLine = lines[i];
            multilineContent.push(nextLine);
            endLineNum = i;
            if (nextLine.trim().endsWith("'")) {
              const lastContentLine = multilineContent.pop();
              if (lastContentLine) {
                multilineContent.push(lastContentLine.substring(0, lastContentLine.lastIndexOf("'")));
              }
              break;
            }
            i++;
          }
          accumulatedValue = multilineContent.join('\n');
          entries.push({
            key,
            value: accumulatedValue,
            isCommentOrEmpty: false,
            isMultilineQuoted: true,
            originalLineNumStart: currentLineNum,
            originalLineNumEnd: endLineNum
          });
        }
      } else {
        entries.push({
          key,
          value: valueString.trim(),
          isCommentOrEmpty: false,
          isMultilineQuoted: false,
          originalLineNumStart: currentLineNum,
          originalLineNumEnd: currentLineNum
        });
      }
      i++;
    }
    return entries;
  };

  // Build env string from entries
  const buildEnvString = (entries: EnvEntry[]): string => {
    return entries.map(entry => {
      if (entry.isCommentOrEmpty) {
        return entry.value;
      }
      if (entry.isMultilineQuoted || entry.value.includes('\n')) {
        return `${entry.key}='${entry.value}'`;
      }
      return `${entry.key}=${entry.value}`;
    }).join('\n');
  };

  // Load base config
  const loadBaseConfig = async () => {
    try {
      setBaseConfigLoading(true);
      const data: ApiResponse<string> = await apiFetch(`${API_BASE}/admin_api/config/main`);
      if (data.content) {
        setBaseConfigEntries(parseEnvToList(data.content));
      }
    } catch (error: any) {
      setBaseConfigStatus(`加载失败: ${error.message}`);
    } finally {
      setBaseConfigLoading(false);
    }
  };

  // Save base config
  const saveBaseConfig = async () => {
    try {
      setBaseConfigStatus("正在保存...");
      const content = buildEnvString(baseConfigEntries);
      await apiFetch(`${API_BASE}/admin_api/config/main`, {
        method: 'POST',
        body: JSON.stringify({ content }),
      });
      showMessage('全局配置已保存！部分更改可能需要重启服务生效。', 'success');
      await loadBaseConfig();
    } catch (error: any) {
      setBaseConfigStatus(`保存失败: ${error.message}`);
      showMessage(`保存失败: ${error.message}`, 'error');
    }
  };

  // Load plugins
  const loadPlugins = async () => {
    try {
      const data: Plugin[] = await apiFetch(`${API_BASE}/admin_api/plugins`);
      setPlugins(data);

      // Parse plugin configs
      const configs: Record<string, EnvEntry[]> = {};
      for (const plugin of data) {
        if (plugin.configEnvContent) {
          configs[plugin.name] = parseEnvToList(plugin.configEnvContent);
        }
      }
      setPluginConfigEntries(configs);
    } catch (error: any) {
      showMessage(`加载插件失败: ${error.message}`, 'error');
    }
  };

  // Save plugin config
  const savePluginConfig = async (pluginName: string) => {
    try {
      const entries = pluginConfigEntries[pluginName] || [];
      const content = buildEnvString(entries);
      await apiFetch(`${API_BASE}/admin_api/plugins/${pluginName}/config`, {
        method: 'POST',
        body: JSON.stringify({ content }),
      });
      showMessage('插件配置已保存', 'success');
    } catch (error: any) {
      showMessage(`保存失败: ${error.message}`, 'error');
    }
  };

  // Toggle plugin enable/disable
  const togglePlugin = async (pluginName: string, enable: boolean) => {
    try {
      await apiFetch(`${API_BASE}/admin_api/plugins/${pluginName}/toggle`, {
        method: 'POST',
        body: JSON.stringify({ enable }),
      });
      showMessage(`插件已${enable ? '启用' : '禁用'}，建议重启服务器以完全生效`, 'success');
      await loadPlugins();
    } catch (error: any) {
      showMessage(`操作失败: ${error.message}`, 'error');
    }
  };

  // Save command description
  const saveCommandDescription = async (pluginName: string, commandIdentifier: string, description: string) => {
    try {
      await apiFetch(`${API_BASE}/admin_api/plugins/${pluginName}/commands/${commandIdentifier}/description`, {
        method: 'POST',
        body: JSON.stringify({ description }),
      });
      setPluginEditingCommandDescriptions(prev => {
        const newState = { ...prev };
        if (newState[pluginName]) {
          delete newState[pluginName][commandIdentifier];
        }
        return newState;
      });
      showMessage('指令描述已保存', 'success');
    } catch (error: any) {
      showMessage(`保存失败: ${error.message}`, 'error');
    }
  };

  // Update config entry value
  const updateConfigValue = (entries: EnvEntry[], index: number, newValue: string) => {
    const newEntries = [...entries];
    newEntries[index] = { ...newEntries[index], value: newValue };
    return newEntries;
  };

  // Daily Notes functions
  const loadNoteFolders = async () => {
    try {
      const data: { folders: string[] } = await apiFetch(`${API_BASE}/admin_api/dailynotes/folders`);
      if (data.folders) {
        setNoteFolders(data.folders);
        if (data.folders.length > 0 && !activeFolder) {
          setActiveFolder(data.folders[0]);
        }
      }
    } catch (error: any) {
      setNotesStatus(`加载文件夹失败: ${error.message}`);
    }
  };

  const loadNotes = async (folder: string) => {
    try {
      const data: { notes: DailyNote[] } = await apiFetch(`${API_BASE}/admin_api/dailynotes/folder/${folder}`);
      if (data.notes) {
        setNotes(data.notes);
      }
    } catch (error: any) {
      setNotesStatus(`加载日记失败: ${error.message}`);
    }
  };

  const loadNoteContent = async (folder: string, fileName: string) => {
    try {
      const data: ApiResponse<{ content: string }> = await apiFetch(`${API_BASE}/admin_api/dailynotes/note/${folder}/${fileName}`);
      if (data.content?.content !== undefined) {
        setNoteContent(data.content.content);
        setEditingNote({ name: fileName, folderName: folder, lastModified: '', preview: '' });
      }
    } catch (error: any) {
      showMessage(`加载日记内容失败: ${error.message}`, 'error');
    }
  };

  const saveNoteContent = async () => {
    if (!editingNote) return;
    try {
      await apiFetch(`${API_BASE}/admin_api/dailynotes/note/${editingNote.folderName}/${editingNote.name}`, {
        method: 'POST',
        body: JSON.stringify({ content: noteContent }),
      });
      showMessage('日记已保存', 'success');
      setEditingNote(null);
      await loadNotes(editingNote.folderName);
    } catch (error: any) {
      showMessage(`保存失败: ${error.message}`, 'error');
    }
  };

  const deleteNotes = async () => {
    if (selectedNotes.size === 0) return;
    try {
      const notesToDelete = Array.from(selectedNotes).map(key => {
        const [folder, file] = key.split('/');
        return { folder, file };
      });
      await apiFetch(`${API_BASE}/admin_api/dailynotes/delete-batch`, {
        method: 'POST',
        body: JSON.stringify({ notesToDelete }),
      });
      showMessage(`已删除 ${selectedNotes.size} 条日记`, 'success');
      setSelectedNotes(new Set());
      await loadNotes(activeFolder);
    } catch (error: any) {
      showMessage(`删除失败: ${error.message}`, 'error');
    }
  };

  const searchNotes = async () => {
    if (!searchTerm.trim()) return;
    try {
      const folderParam = activeFolder ? `?folder=${activeFolder}` : '';
      const data: { notes: DailyNote[] } = await apiFetch(`${API_BASE}/admin_api/dailynotes/search?term=${encodeURIComponent(searchTerm)}${folderParam}`);
      if (data.notes) {
        setNotes(data.notes);
      }
    } catch (error: any) {
      showMessage(`搜索失败: ${error.message}`, 'error');
    }
  };

  const restartServer = async () => {
    if (!confirm('确定要重启服务器吗？')) return;
    try {
      await apiFetch(`${API_BASE}/admin_api/server/restart`, { method: 'POST' });
      showMessage('服务器重启命令已发送', 'success');
    } catch (error: any) {
      showMessage(`重启失败: ${error.message}`, 'error');
    }
  };

  // Render config entry form group
  const renderConfigEntry = (
    entries: EnvEntry[],
    index: number,
    onUpdate: (index: number, value: string) => void,
    onDelete?: (index: number) => void
  ) => {
    const entry = entries[index];
    if (entry.isCommentOrEmpty) {
      return (
        <div key={index} className={`text-sm font-mono ${
          theme === 'dark' ? 'text-gray-500' : 'text-gray-500'
        }`}>
          {entry.value || '(空行)'}
        </div>
      );
    }

    const inferredType = /^(true|false)$/i.test(entry.value) ? 'boolean' :
      !isNaN(parseFloat(entry.value)) && isFinite(parseFloat(entry.value)) ? 'number' : 'text';

    return (
      <div key={index} className={`p-4 rounded-lg border ${
        theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-gray-50 border-gray-200'
      }`}>
        <label className="block mb-2">
          <span className={`font-semibold ${
            theme === 'dark' ? 'text-gray-200' : 'text-gray-800'
          }`}>{entry.key}</span>
        </label>
        {inferredType === 'boolean' ? (
          <div className="flex items-center gap-3">
            <label className="relative inline-block w-12 h-6">
              <input
                type="checkbox"
                checked={entry.value === 'true'}
                onChange={(e) => onUpdate(index, e.target.checked ? 'true' : 'false')}
                className="sr-only peer"
              />
              <div className={`absolute inset-0 rounded-full transition-colors peer-checked:bg-blue-500 cursor-pointer ${
                theme === 'dark' ? 'bg-gray-600' : 'bg-gray-300'
              }`} />
              <div className="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-6 shadow" />
            </label>
            <span className={`text-sm ${
              theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
            }`}>
              {entry.value === 'true' ? '启用' : '禁用'}
            </span>
          </div>
        ) : (
          <textarea
            value={entry.value}
            onChange={(e) => onUpdate(index, e.target.value)}
            rows={(entry.isMultilineQuoted || entry.value.includes('\n')) ? 4 : 1}
            className={`w-full p-3 rounded border focus:outline-none focus:ring-2 focus:ring-blue-500/30 font-mono text-sm resize-y ${
              theme === 'dark'
                ? 'bg-gray-900 text-gray-200 border-gray-700 focus:border-blue-600/75'
                : 'bg-white text-gray-900 border-gray-300 focus:border-blue-500/70'
            }`}
          />
        )}
        {onDelete && (
          <button
            onClick={() => onDelete(index)}
            className="mt-2 px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600 transition-colors"
          >
            删除
          </button>
        )}
      </div>
    );
  };

  // Render main content
  const renderMainContent = () => {
    if (activeSection === 'base-config') {
      return (
        <section className="animate-in fade-in slide-in-from-bottom-4 duration-500">
          <h2 className={`text-2xl font-bold mb-6 pb-3 border-b-2 ${
            theme === 'dark' ? 'text-blue-400 border-blue-400' : 'text-blue-600 border-blue-600'
          }`}>
            全局基础配置 (config.env)
          </h2>
          {baseConfigLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className={`animate-spin w-10 h-10 border-4 rounded-full ${
                theme === 'dark' ? 'border-gray-700 border-t-blue-400' : 'border-gray-200 border-t-blue-600'
              }`} />
            </div>
          ) : (
            <div className="space-y-5">
              {baseConfigEntries.map((_, index) =>
                renderConfigEntry(
                  baseConfigEntries,
                  index,
                  (i, v) => setBaseConfigEntries(updateConfigValue(baseConfigEntries, i, v))
                )
              )}
              <button
                onClick={saveBaseConfig}
                className="w-full py-3 bg-green-500 text-white rounded-lg font-semibold hover:bg-green-600 transition-colors"
              >
                保存全局配置
              </button>
              {baseConfigStatus && (
                <p className={`text-sm text-center ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>{baseConfigStatus}</p>
              )}
            </div>
          )}
        </section>
      );
    }

    if (activeSection === 'daily-notes-manager') {
      return (
        <section className="animate-in fade-in slide-in-from-bottom-4 duration-500">
          <h2 className={`text-2xl font-bold mb-6 pb-3 border-b-2 ${
            theme === 'dark' ? 'text-blue-400 border-blue-400' : 'text-blue-600 border-blue-600'
          }`}>
            日记管理
          </h2>
          {editingNote ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className={`text-xl font-semibold ${theme === 'dark' ? 'text-gray-200' : 'text-gray-700'}`}>编辑日记</h3>
                <button
                  onClick={() => setEditingNote(null)}
                  className={`p-2 rounded-lg transition-colors ${theme === 'dark' ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <textarea
                value={noteContent}
                onChange={(e) => setNoteContent(e.target.value)}
                className={`w-full min-h-[300px] p-4 rounded-lg border focus:outline-none resize-y font-mono ${
                  theme === 'dark'
                    ? 'bg-gray-900 text-gray-200 border-gray-700 focus:border-blue-500'
                    : 'bg-white text-gray-900 border-gray-300 focus:border-blue-500'
                }`}
                spellCheck={false}
              />
              <div className="flex gap-3">
                <button
                  onClick={saveNoteContent}
                  className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
                >
                  <Save className="w-4 h-4" />
                  保存日记
                </button>
                <button
                  onClick={() => setEditingNote(null)}
                  className="px-4 py-2 bg-gray-400 text-white rounded-lg hover:bg-gray-500 transition-colors"
                >
                  取消编辑
                </button>
              </div>
            </div>
          ) : (
            <div className="flex gap-5">
              {/* Folders sidebar */}
              <div className={`w-48 flex-shrink-0 p-4 rounded-lg border ${
                theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-gray-50 border-gray-200'
              }`}>
                <h3 className={`text-lg font-semibold mb-3 pb-2 border-b border-dashed ${
                  theme === 'dark' ? 'text-gray-200 border-gray-600' : 'text-gray-700 border-gray-300'
                }`}>角色日记</h3>
                <ul className="space-y-1">
                  {noteFolders.map(folder => (
                    <li
                      key={folder}
                      onClick={() => setActiveFolder(folder)}
                      className={`px-3 py-2 rounded cursor-pointer transition-colors ${
                        activeFolder === folder
                          ? 'bg-blue-100 text-blue-700 font-semibold'
                          : theme === 'dark'
                            ? 'text-gray-400 hover:bg-gray-700 hover:text-gray-200'
                            : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                      }`}
                    >
                      {folder}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Notes content */}
              <div className="flex-1 space-y-4">
                {/* Toolbar */}
                <div className={`flex items-center gap-3 p-3 rounded-lg border ${
                  theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-gray-50 border-gray-200'
                }`}>
                  <div className="flex-1 relative">
                    <Search className={`absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 ${
                      theme === 'dark' ? 'text-gray-500' : 'text-gray-400'
                    }`} />
                    <input
                      type="search"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && searchNotes()}
                      placeholder="搜索日记..."
                      className={`w-full pl-10 pr-4 py-2 rounded border focus:outline-none ${
                        theme === 'dark'
                          ? 'bg-gray-900 text-gray-200 border-gray-700 focus:border-blue-500'
                          : 'bg-white text-gray-900 border-gray-300 focus:border-blue-500'
                      }`}
                    />
                  </div>
                  <button
                    onClick={deleteNotes}
                    disabled={selectedNotes.size === 0}
                    className="flex items-center gap-2 px-3 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
                  >
                    <Trash2 className="w-4 h-4" />
                    批量删除 ({selectedNotes.size})
                  </button>
                </div>

                {/* Notes grid */}
                {notes.length === 0 ? (
                  <div className={`flex flex-col items-center justify-center py-16 ${
                    theme === 'dark' ? 'text-gray-500' : 'text-gray-400'
                  }`}>
                    <FileText className="w-16 h-16 mb-4 opacity-50" />
                    <p className="text-lg">当前角色中没有日记文件</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {notes.map(note => {
                      const key = `${note.folderName}/${note.name}`;
                      const isSelected = selectedNotes.has(key);
                      return (
                        <div
                          key={key}
                          onClick={() => loadNoteContent(note.folderName, note.name)}
                          onContextMenu={(e) => {
                            e.preventDefault();
                            setSelectedNotes(prev => {
                              const newSet = new Set(prev);
                              if (newSet.has(key)) {
                                newSet.delete(key);
                              } else {
                                newSet.add(key);
                              }
                              return newSet;
                            });
                          }}
                          className={`p-4 rounded-lg border cursor-pointer transition-all hover:shadow-md hover:-translate-y-1 ${
                            theme === 'dark'
                              ? 'bg-gray-800 ' + (isSelected ? 'border-l-4 border-l-blue-400 shadow-md shadow-blue-400/20' : 'border-gray-700')
                              : 'bg-white ' + (isSelected ? 'border-l-4 border-l-blue-500 shadow-md shadow-blue-500/20' : 'border-gray-200')
                          }`}
                        >
                          <h4 className={`font-semibold mb-2 break-all ${theme === 'dark' ? 'text-gray-200' : 'text-gray-800'}`}>{note.name}</h4>
                          <p className={`text-sm line-clamp-3 mb-3 min-h-[60px] ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>{note.preview}</p>
                          <p className={`text-xs ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`}>{new Date(note.lastModified).toLocaleString()}</p>
                        </div>
                      );
                    })}
                  </div>
                )}

                {notesStatus && <p className={`text-sm text-center ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>{notesStatus}</p>}
              </div>
            </div>
          )}
        </section>
      );
    }

    // Plugin config
    if (activePlugin) {
      const plugin = plugins.find(p => p.name === activePlugin);
      if (!plugin) return null;

      const entries = pluginConfigEntries[activePlugin] || [];
      const editingCommands = pluginEditingCommandDescriptions[activePlugin] || {};

      return (
        <section className="animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className={`flex justify-between items-center mb-6 pb-3 border-b-2 ${
            theme === 'dark' ? 'border-blue-400' : 'border-blue-600'
          }`}>
            <h2 className={`text-2xl font-bold ${theme === 'dark' ? 'text-blue-400' : 'text-blue-600'}`}>
              {plugin.manifest.displayName || plugin.name}
            </h2>
            <div className="flex items-center gap-3">
              <span className={`text-sm font-medium ${plugin.enabled ? 'text-green-600' : 'text-gray-500'}`}>
                {plugin.enabled ? '已启用' : '已禁用'}
              </span>
              <button
                onClick={() => togglePlugin(plugin.name, !plugin.enabled)}
                className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                  plugin.enabled ? 'bg-green-500' : 'bg-gray-300'
                }`}
                title={plugin.enabled ? '点击禁用插件' : '点击启用插件'}
              >
                <span
                  className={`inline-block h-6 w-6 transform rounded-full bg-white shadow transition-transform ${
                    plugin.enabled ? 'translate-x-7' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>

          {/* Description */}
          {plugin.manifest.description && (
            <div className={`mb-6 p-4 rounded-lg border ${
              theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-gray-50 border-gray-200'
            }`}>
              <p className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>{plugin.manifest.description}</p>
            </div>
          )}

          {/* Config */}
          {entries.length > 0 && (
            <div className="mb-6">
              <h3 className={`text-lg font-semibold mb-4 pb-2 border-b border-dashed ${
                theme === 'dark' ? 'text-gray-200 border-gray-600' : 'text-gray-700 border-gray-300'
              }`}>插件配置 (config.env)</h3>
              <div className="space-y-4">
                {entries.map((_, index) =>
                  renderConfigEntry(
                    entries,
                    index,
                    (i, v) => setPluginConfigEntries(prev => ({
                      ...prev,
                      [activePlugin]: updateConfigValue(prev[activePlugin] || [], i, v)
                    }))
                  )
                )}
              </div>
              <button
                onClick={() => savePluginConfig(activePlugin)}
                className="mt-4 w-full py-3 bg-green-500 text-white rounded-lg font-semibold hover:bg-green-600 transition-colors"
              >
                保存插件配置
              </button>
            </div>
          )}

          {/* Invocation Commands */}
          {plugin.manifest.capabilities?.invocationCommands && plugin.manifest.capabilities.invocationCommands.length > 0 && (
            <div className={`mt-8 pt-6 border-t ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'}`}>
              <h3 className={`text-xl font-semibold mb-4 pb-2 border-b border-dashed ${
                theme === 'dark' ? 'text-gray-200 border-gray-600' : 'text-gray-700 border-gray-300'
              }`}>AI 指令描述</h3>
              <div className="space-y-6">
                {plugin.manifest.capabilities.invocationCommands.map((cmd, idx) => {
                  const isEditing = editingCommands.hasOwnProperty(cmd.commandIdentifier);
                  return (
                    <div key={idx} className={`p-5 rounded-lg border ${
                      theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-gray-50 border-gray-200'
                    }`}>
                      <h4 className={`text-lg font-semibold mb-2 ${theme === 'dark' ? 'text-gray-200' : 'text-gray-800'}`}>{cmd.commandIdentifier}</h4>
                      <p className={`text-sm mb-3 ${theme === 'dark' ? 'text-gray-500' : 'text-gray-500'}`}>指令: {cmd.command}</p>
                      {isEditing ? (
                        <div className="space-y-3">
                          <textarea
                            value={editingCommands[cmd.commandIdentifier]}
                            onChange={(e) => setPluginEditingCommandDescriptions(prev => ({
                              ...prev,
                              [activePlugin]: { ...prev[activePlugin], [cmd.commandIdentifier]: e.target.value }
                            }))}
                            rows={4}
                            className={`w-full p-3 rounded border focus:outline-none resize-y ${
                              theme === 'dark'
                                ? 'bg-gray-900 text-gray-200 border-gray-700 focus:border-blue-500'
                                : 'bg-white text-gray-900 border-gray-300 focus:border-blue-500'
                            }`}
                          />
                          <div className="flex gap-2">
                            <button
                              onClick={() => saveCommandDescription(activePlugin, cmd.commandIdentifier, editingCommands[cmd.commandIdentifier])}
                              className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
                            >
                              保存描述
                            </button>
                            <button
                              onClick={() => setPluginEditingCommandDescriptions(prev => {
                                const newState = { ...prev };
                                if (newState[activePlugin]) {
                                  delete newState[activePlugin][cmd.commandIdentifier];
                                }
                                return newState;
                              })}
                              className="px-4 py-2 bg-gray-400 text-white rounded-lg hover:bg-gray-500 transition-colors"
                            >
                              取消
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex justify-between items-start">
                          <p className={`flex-1 mr-4 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>{cmd.description}</p>
                          <button
                            onClick={() => setPluginEditingCommandDescriptions(prev => ({
                              ...prev,
                              [activePlugin]: { ...prev[activePlugin], [cmd.commandIdentifier]: cmd.description }
                            }))}
                            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm whitespace-nowrap"
                          >
                            编辑描述
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </section>
      );
    }

    return null;
  };

  return (
    <div className={`min-h-screen pt-[52px] ${
      theme === 'dark' ? 'bg-gray-950 text-gray-200' : 'bg-slate-100 text-slate-700'
    }`}>
      {/* Top bar */}
      <header className={`fixed top-0 left-0 right-0 z-50 h-[52px] backdrop-blur-md border-b shadow-sm ${
        theme === 'dark'
          ? 'bg-gray-800/80 border-gray-700'
          : 'bg-white/80 border-slate-200'
      }`}>
        <div className="h-full max-w-[1600px] mx-auto px-5 flex justify-between items-center">
          <span className={`text-xl font-semibold ${
            theme === 'dark' ? 'text-blue-400' : 'text-blue-500'
          }`}>MeetWith</span>
          <button
            onClick={restartServer}
            className={`px-4 py-2 rounded-lg transition-colors text-sm font-semibold ${
              theme === 'dark'
                ? 'bg-red-400 text-white hover:bg-red-500'
                : 'bg-red-500 text-white hover:bg-red-600'
            }`}
          >
            重启服务器
          </button>
        </div>
      </header>

      {/* Message popup */}
      {message && (
        <div className={`fixed bottom-10 left-1/2 -translate-x-1/2 px-7 py-4 rounded-lg shadow-lg text-white font-medium transition-all duration-300 z-[1001] ${
          message.type === 'success' ? 'bg-green-500' :
          message.type === 'error' ? 'bg-red-500' : 'bg-gray-700'
        }`}>
          {message.text}
        </div>
      )}

      {/* Main container */}
      <div className={`flex max-w-[1600px] mx-auto my-5 rounded-xl shadow-md overflow-hidden min-h-[calc(100vh-62px)] ${
        theme === 'dark' ? 'bg-gray-800' : 'bg-white'
      }`}>
        {/* Sidebar */}
        <aside className={`w-[280px] flex-shrink-0 p-6 border-r overflow-y-auto max-h-[calc(100vh-62px)] ${
          theme === 'dark' ? 'bg-gray-800 border-r-gray-700' : 'bg-slate-100 border-r-slate-200'
        }`}>
          <h1 className={`text-2xl font-bold text-center mb-8 tracking-wide ${
            theme === 'dark' ? 'text-blue-400' : 'text-blue-500'
          }`}>配置中心</h1>
          <nav>
            <ul className="space-y-2">
              <li>
                <button
                  onClick={() => { setActiveSection('base-config'); setActivePlugin(null); }}
                  className={`w-full text-left px-5 py-3 rounded-lg transition-all duration-200 font-medium ${
                    activeSection === 'base-config' && !activePlugin
                      ? (theme === 'dark'
                          ? 'bg-gray-700 text-blue-400 shadow-md border-l-4 border-l-blue-400'
                          : 'bg-slate-200 text-blue-500 shadow-md border-l-4 border-l-blue-500')
                      : (theme === 'dark'
                          ? 'text-gray-400 hover:bg-gray-700 hover:text-gray-200'
                          : 'text-slate-600 hover:bg-slate-200 hover:text-slate-700')
                  }`}
                >
                  全局基础配置
                </button>
              </li>
              <li>
                <button
                  onClick={() => { setActiveSection('daily-notes-manager'); setActivePlugin(null); }}
                  className={`w-full text-left px-5 py-3 rounded-lg transition-all duration-200 font-medium ${
                    activeSection === 'daily-notes-manager'
                      ? (theme === 'dark'
                          ? 'bg-gray-700 text-blue-400 shadow-md border-l-4 border-l-blue-400'
                          : 'bg-slate-200 text-blue-500 shadow-md border-l-4 border-l-blue-500')
                      : (theme === 'dark'
                          ? 'text-gray-400 hover:bg-gray-700 hover:text-gray-200'
                          : 'text-slate-600 hover:bg-slate-200 hover:text-slate-700')
                  }`}
                >
                  日记管理
                </button>
              </li>
              {plugins.map(plugin => (
                <li key={plugin.name}>
                  <button
                    onClick={() => { setActiveSection(plugin.name); setActivePlugin(plugin.name); }}
                    className={`w-full text-left px-5 py-3 rounded-lg transition-all duration-200 font-medium ${
                      activePlugin === plugin.name
                        ? (theme === 'dark'
                            ? 'bg-gray-700 text-blue-400 shadow-md border-l-4 border-l-blue-400'
                            : 'bg-slate-200 text-blue-500 shadow-md border-l-4 border-l-blue-500')
                        : (theme === 'dark'
                            ? 'text-gray-400 hover:bg-gray-700 hover:text-gray-200'
                            : 'text-slate-600 hover:bg-slate-200 hover:text-slate-700')
                    }`}
                  >
                    {plugin.manifest.displayName || plugin.name}
                  </button>
                </li>
              ))}
            </ul>
          </nav>

          {/* Back button */}
          <Link to="/" className="mt-6 block">
            <button className={`w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              theme === 'dark'
                ? 'bg-gray-700 text-gray-400 hover:bg-gray-700 hover:text-gray-200'
                : 'bg-slate-200 text-slate-600 hover:bg-slate-200 hover:text-slate-700'
            }`}>
              <ChevronLeft className="w-4 h-4" />
              返回聊天
            </button>
          </Link>
        </aside>

        {/* Main content */}
        <main className={`flex-1 p-10 overflow-y-auto max-h-[calc(100vh-62px)] ${
          theme === 'dark' ? 'bg-gray-950' : 'bg-slate-100'
        }`}>
          {renderMainContent()}
        </main>
      </div>
    </div>
  );
}
