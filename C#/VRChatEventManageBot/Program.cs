using Discord.Commands;
using Discord.Interactions;
using Discord.WebSocket;
using Discord;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using VRChatEventManageBot;
using LogExtentions;
using Microsoft.Extensions.Configuration;

public class Program
{
    public static DiscordSocketClient _client;
    public static CommandService _commands;
    public static IServiceProvider _services;

    public static Task Main(string[] args) => new Program().MainAsync();

    public async Task MainAsync()
    {
        Console.Title = "VRChatEventManageBot";

        using IHost host = Host.CreateDefaultBuilder()
            .ConfigureServices((_, services) =>
                services

                    .AddSingleton(x => new DiscordSocketClient(new DiscordSocketConfig
                    {
                        GatewayIntents = Discord.GatewayIntents.All,
                        LogGatewayIntentWarnings = true,
                        AlwaysDownloadUsers = true,

                        LogLevel = LogSeverity.Debug
                    }))

                   /* .AddSingleton(x =>
                    {
                        var config = new InteractionServiceConfig
                        {
                            LocalizationManager = new JsonLocalizationManager("locales", "command"),
                            // 必要なら追加設定  
                        };
                        return new InteractionService(x.GetRequiredService<DiscordSocketClient>(), config);
                    })*/
                   .AddSingleton(x => new InteractionService(x.GetRequiredService<DiscordSocketClient>()))
                    .AddSingleton<InteractionHandler>()

                    .AddHostedService<ConsoleCommandHandler>()
            ) 
            .Build(); 

        await RunAsync(host);
    }

    public async Task RunAsync(IHost host)
    {
        var builder = new ConfigurationBuilder();
        builder.AddJsonFile("appsettings.json", optional: true, reloadOnChange: true);
        var configuration = builder.Build();

        // 設定ファイルからトークンを取得
        string token = configuration["DiscordToken"];

        // トークンが未設定またはデフォルト値の場合、ユーザーに入力を促す
        while (string.IsNullOrWhiteSpace(token) || token == "TokenHere!")
        {
            Log.Error("DiscordTokenが入力されていません。入力してください。");
            token = Console.ReadLine();

            try
            {
                // トークンの検証。失敗時はArgumentExceptionがスローされる
                Discord.TokenUtils.ValidateToken(tokenType: TokenType.Bot, token: token);
            }
            catch (ArgumentException)
            {
                Log.Error("適切なTokenを入力してください。");
                token = null; // ループ継続
            }
        }

        configuration["DiscordToken"] = token;
        // 設定ファイルに保存するコードを追加
        var configFilePath = "appsettings.json";
        File.WriteAllText(configFilePath, System.Text.Json.JsonSerializer.Serialize(configuration.GetChildren().ToDictionary(c => c.Key, c => c.Value), new System.Text.Json.JsonSerializerOptions { WriteIndented = true }));




        Console.InputEncoding = System.Text.Encoding.UTF8;
        Console.OutputEncoding = System.Text.Encoding.UTF8;
        using IServiceScope serviceScope = host.Services.CreateScope();
        IServiceProvider provider = serviceScope.ServiceProvider;

        _services = provider;

        var commands = provider.GetRequiredService<InteractionService>();
        try
        {
            _client = provider.GetRequiredService<DiscordSocketClient>();
            Log.Info("初期化に成功");

        }
        catch (Exception ex)
        {

            Log.Error($"{ex}");
        }

        _services = provider.GetRequiredService<IServiceProvider>();

        try
        {

            await provider.GetRequiredService<InteractionHandler>().InitializeAsync();
            Log.Info("Commands registered successfully.");
        }
        catch (Exception ex)
        {
            Log.Error($"{ex}");
        }

        _client.Ready += async () =>
        {
            try
            {

                using IServiceScope serviceScope = host.Services.CreateScope();
                IServiceProvider provider = serviceScope.ServiceProvider;

                /* var commands = provider.GetRequiredService<InteractionService>();
                 commands.LocalizationManager = new JsonLocalizationManager("locales", "command"); */
                await commands.RegisterCommandsGloballyAsync(true);
                Log.Info("コマンドをグローバルに登録");
            }
            catch (Exception e)
            {
                Log.Error(e.Message);
            }
        };
        _client.Ready += () =>
        {
            _ = Task.Run(async () => await ClientReady());
            return Task.CompletedTask;
        };
        _client.Log += DiscordLog;

        await _client.LoginAsync(Discord.TokenType.Bot, token); 
        await _client.StartAsync();

        await host.StartAsync();

        Log.Info("すべてのサービスが開始されました");

        // アプリケーションを実行し続ける  
        await host.WaitForShutdownAsync();
    }

    private async Task ClientReady()
    {
        await DiscordUpgradeDiscordState();
    }
    private async Task DiscordUpgradeDiscordState()
    {
        while (true)
        {

            int ping = _client.Latency;
            int connectedChannels = GetConnectedChannelCount();
            int guildCount = _client.Guilds.Count;

            string statusMessage = $"{ping}ms | {connectedChannels} connected | {guildCount} servers";

            await _client.SetActivityAsync(new Game(statusMessage, ActivityType.Listening));
            Log.Info($"discord state updated {statusMessage}");
            await Task.Delay(TimeSpan.FromSeconds(120));
        }
    }
    private int GetConnectedChannelCount()
    {
        return _client.Guilds
            .SelectMany(g => g.VoiceChannels)
            .Count(vc => vc.ConnectedUsers.Any(u => u.Id == _client.CurrentUser.Id));
    }
    private async Task DiscordLog(LogMessage arg)
    {
        switch (arg.Severity)
        {
            case LogSeverity.Critical:
                Log.Error($"[Critical] [Discord] {arg.Message}");
                break;
            case LogSeverity.Error:
                Log.Error($"[Discord] {arg.Message}");
                break;
            case LogSeverity.Warning:
                Log.Warn($"[Discord] {arg.Message}");
                break;
            case LogSeverity.Info:
                Log.Info($"[Discord] {arg.Message}");
                break;
            case LogSeverity.Verbose:
                Log.Debug($"[Verbose] [Discord] {arg.Message}");
                break;
            case LogSeverity.Debug:
                Log.Debug($"[Discord] {arg.Message}");
                break;
            default:
                break;
        }
    }
}
