import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Link } from "react-router-dom";

const API_BASE = "";

interface Plugin {
  name: string;
  manifest: {
    displayName?: string;
    name: string;
    description?: string;
  };
  enabled: boolean;
  configEnvContent?: string;
}

interface ApiResponse<T> {
  content?: T;
  message?: string;
  error?: string;
}

export function Settings() {
  const [mainConfig, setMainConfig] = useState("");
  const [mainConfigStatus, setMainConfigStatus] = useState("");
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [pluginStatus, setPluginStatus] = useState("");
  const [editingDescriptions, setEditingDescriptions] = useState<Record<string, string>>({});

  // 加载主配置
  useEffect(() => {
    loadMainConfig();
  }, []);

  // 加载插件列表
  useEffect(() => {
    loadPlugins();
  }, []);

  const loadMainConfig = async () => {
    try {
      setMainConfigStatus("正在加载主配置...");
      const response = await fetch(`${API_BASE}/admin_api/config/main`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data: ApiResponse<string> = await response.json();
      if (data.content) {
        setMainConfig(data.content);
        setMainConfigStatus("主配置已加载");
      }
    } catch (error: any) {
      setMainConfigStatus(`加载失败: ${error.message}`);
    }
  };

  const saveMainConfig = async () => {
    try {
      setMainConfigStatus("正在保存主配置...");
      const response = await fetch(`${API_BASE}/admin_api/config/main`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: mainConfig }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data: ApiResponse<string> = await response.json();
      setMainConfigStatus(data.message || "主配置已保存");
      await loadMainConfig();
    } catch (error: any) {
      setMainConfigStatus(`保存失败: ${error.message}`);
    }
  };

  const loadPlugins = async () => {
    try {
      setPluginStatus("正在加载插件列表...");
      const response = await fetch(`${API_BASE}/admin_api/plugins`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data: Plugin[] = await response.json();
      setPlugins(data);
      setPluginStatus(data.length === 0 ? "未找到插件" : "插件列表已加载");
    } catch (error: any) {
      setPluginStatus(`加载失败: ${error.message}`);
    }
  };

  const togglePlugin = async (pluginName: string, enable: boolean) => {
    try {
      setPluginStatus(`正在${enable ? "启用" : "禁用"}插件 ${pluginName}...`);
      const response = await fetch(`${API_BASE}/admin_api/plugins/${pluginName}/toggle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enable }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data: ApiResponse<string> = await response.json();
      setPluginStatus(data.message || `插件已${enable ? "启用" : "禁用"}`);
      await loadPlugins();
    } catch (error: any) {
      setPluginStatus(`操作失败: ${error.message}`);
    }
  };

  const savePluginDescription = async (pluginName: string, description: string) => {
    try {
      setPluginStatus(`正在保存 ${pluginName} 的描述...`);
      const response = await fetch(`${API_BASE}/admin_api/plugins/${pluginName}/description`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data: ApiResponse<string> = await response.json();
      setPluginStatus(data.message || "描述已保存");
      setEditingDescriptions((prev) => {
        const newState = { ...prev };
        delete newState[pluginName];
        return newState;
      });
      await loadPlugins();
    } catch (error: any) {
      setPluginStatus(`保存失败: ${error.message}`);
    }
  };

  const savePluginConfig = async (pluginName: string, content: string) => {
    try {
      setPluginStatus(`正在保存 ${pluginName} 的配置...`);
      const response = await fetch(`${API_BASE}/admin_api/plugins/${pluginName}/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data: ApiResponse<string> = await response.json();
      setPluginStatus(data.message || "插件配置已保存");
    } catch (error: any) {
      setPluginStatus(`保存失败: ${error.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-background p-8">
      {/* 返回按钮 */}
      <Link to="/" className="inline-block mb-4">
        <Button variant="outline" size="sm">
          ← 返回聊天
        </Button>
      </Link>

      <div className="max-w-5xl mx-auto space-y-8">
        <h1 className="text-3xl font-bold text-center">服务器管理面板</h1>

        {/* 主配置 */}
        <section className="rounded-lg border bg-card p-6 shadow-sm">
          <h2 className="text-xl font-semibold mb-4 pb-2 border-b">主配置 (config.env)</h2>
          <Textarea
            value={mainConfig}
            onChange={(e) => setMainConfig(e.target.value)}
            rows={15}
            className="font-mono text-sm mb-4"
          />
          <div className="flex items-center gap-4">
            <Button onClick={saveMainConfig}>保存主配置</Button>
            <span className="text-sm text-muted-foreground">{mainConfigStatus}</span>
          </div>
        </section>

        {/* 插件管理 */}
        <section className="rounded-lg border bg-card p-6 shadow-sm">
          <h2 className="text-xl font-semibold mb-4 pb-2 border-b">插件管理</h2>
          <p className="text-sm text-muted-foreground mb-4">{pluginStatus}</p>

          <ScrollArea className="h-[600px] pr-4">
            <div className="space-y-4">
              {plugins.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">未找到任何插件</p>
              ) : (
                plugins.map((plugin) => {
                  const isEditing = editingDescriptions.hasOwnProperty(plugin.name);
                  const currentDescription = isEditing
                    ? editingDescriptions[plugin.name]
                    : plugin.manifest.description || "";

                  return (
                    <div
                      key={plugin.name}
                      className="rounded-lg border bg-muted/30 p-4 space-y-3"
                    >
                      {/* 插件标题和状态 */}
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="font-semibold text-lg">
                            {plugin.manifest.displayName || plugin.name}
                            <span className="text-sm font-normal text-muted-foreground ml-2">
                              ({plugin.name})
                            </span>
                          </h3>
                          <p className="text-sm text-muted-foreground">
                            状态:{" "}
                            <span
                              className={
                                plugin.enabled ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
                              }
                            >
                              {plugin.enabled ? "已启用" : "已禁用"}
                            </span>
                          </p>
                        </div>
                        <Button
                          variant={plugin.enabled ? "destructive" : "default"}
                          size="sm"
                          onClick={() => togglePlugin(plugin.name, !plugin.enabled)}
                        >
                          {plugin.enabled ? "禁用插件" : "启用插件"}
                        </Button>
                      </div>

                      {/* 描述编辑 */}
                      <div className="space-y-2">
                        <p className="text-sm font-medium">描述:</p>
                        {isEditing ? (
                          <div className="space-y-2">
                            <Textarea
                              value={currentDescription}
                              onChange={(e) =>
                                setEditingDescriptions((prev) => ({
                                  ...prev,
                                  [plugin.name]: e.target.value,
                                }))
                              }
                              rows={2}
                              className="text-sm"
                            />
                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                onClick={() => savePluginDescription(plugin.name, currentDescription)}
                              >
                                保存描述
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => {
                                  setEditingDescriptions((prev) => {
                                    const newState = { ...prev };
                                    delete newState[plugin.name];
                                    return newState;
                                  });
                                }}
                              >
                                取消编辑
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2">
                            <p className="text-sm text-muted-foreground flex-1">
                              {plugin.manifest.description || "(无描述)"}
                            </p>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() =>
                                setEditingDescriptions((prev) => ({
                                  ...prev,
                                  [plugin.name]: plugin.manifest.description || "",
                                }))
                              }
                            >
                              编辑描述
                            </Button>
                          </div>
                        )}
                      </div>

                      {/* 插件配置 */}
                      <div className="space-y-2">
                        <h4 className="text-sm font-medium">插件配置 (config.env)</h4>
                        <Textarea
                          defaultValue={plugin.configEnvContent || ""}
                          rows={5}
                          placeholder="此插件没有独立的 config.env 文件"
                          className="font-mono text-sm"
                        />
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={(e) => {
                            const textarea = (e.target as HTMLElement)
                              .previousElementSibling as HTMLTextAreaElement;
                            if (textarea) savePluginConfig(plugin.name, textarea.value);
                          }}
                        >
                          保存插件配置
                        </Button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </ScrollArea>
        </section>
      </div>
    </div>
  );
}
