using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Discord.WebSocket;

using System;
using System.Threading;
using System.Threading.Tasks;
using LogExtentions;

namespace VRChatEventManageBot
{





        public class ConsoleCommandHandler : BackgroundService
        {
            private readonly ILogger<ConsoleCommandHandler> _logger;
            private readonly DiscordSocketClient _discordClient;

            private readonly IHostApplicationLifetime _applicationLifetime;

            public ConsoleCommandHandler(
                ILogger<ConsoleCommandHandler> logger,
                DiscordSocketClient discordClient,

                IHostApplicationLifetime applicationLifetime)
            {
                _logger = logger;
                _discordClient = discordClient;
                _applicationLifetime = applicationLifetime;
            }

            protected override async Task ExecuteAsync(CancellationToken stoppingToken)
            {
                _logger.LogInformation("Console command handler started. Type 'help' for available commands.");

                while (!stoppingToken.IsCancellationRequested)
                {
                    try
                    {
                        var input = await ReadLineAsync(stoppingToken);

                        if (string.IsNullOrWhiteSpace(input))
                            continue;

                        await ProcessCommandAsync(input.Trim());
                    }
                    catch (OperationCanceledException)
                    {
                        break;
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError(ex, "Error processing console command");
                    }
                }
            }

            private async Task<string> ReadLineAsync(CancellationToken cancellationToken)
            {
                return await Task.Run(() =>
                {
                    while (!cancellationToken.IsCancellationRequested)
                    {
                        if (Console.KeyAvailable)
                        {
                            return Console.ReadLine();
                        }
                        Thread.Sleep(100);
                    }
                    return null;
                }, cancellationToken);
            }

            private async Task ProcessCommandAsync(string command)
            {
                var parts = command.Split(' ', StringSplitOptions.RemoveEmptyEntries);
                if (parts.Length == 0) return;

                var cmd = parts[0].ToLower();

                switch (cmd)
                {
                    case "help":
                        ShowHelp();
                        break;

                    case "status":
                        await ShowStatusAsync();
                        break;

                    case "guilds":
                        ShowGuilds();
                        break;

                    case "gc":
                        ForceGarbageCollection();
                        break;

                    case "stop":
                    case "exit":
                    case "quit":
                        Log.Info("Shutting down...");
                        _applicationLifetime.StopApplication();
                        break;

                    case "reload":
                        Log.Info("Reload functionality not implemented yet.");
                        break;

                    case "clear":
                        Console.Clear();
                        break;

                    default:
                        Log.Warn($"Unknown command: {cmd}. Type 'help' for available commands.");
                        break;
                }
            }

            private void ShowHelp()
            {
                Log.Info("Available commands:");
                Log.Info("  help     - Show this help message");
                Log.Info("  status   - Show bot status");
                Log.Info("  guilds   - Show connected guilds");
                Log.Info("  gc       - Force garbage collection");
                Log.Info("  clear    - Clear console");
                Log.Info("  stop     - Stop the bot");
                Log.Info("  exit     - Stop the bot");
                Log.Info("  quit     - Stop the bot");
            }
           
            private async Task ShowStatusAsync()
            {
                var status = _discordClient.ConnectionState;
                var latency = _discordClient.Latency;
                var guildCount = _discordClient.Guilds.Count;

                Log.Info($"Discord Connection: {_discordClient.ConnectionState}");
                Log.Info($"Latency: {_discordClient.Latency}ms");
                Log.Info($"Connected Guilds: {_discordClient.Guilds.Count}");
                Log.Info($"Memory Usage: {GC.GetTotalMemory(false) / 1024 / 1024} MB");

            }

            private void ShowGuilds()
            {
                Log.Info("Connected Guilds:");
                foreach (var guild in _discordClient.Guilds)
                {
                    Log.Info($"  {guild.Name} (ID: {guild.Id}) - {guild.MemberCount} members");
                }
            }


           
            private void ForceGarbageCollection()
            {
                var beforeMemory = GC.GetTotalMemory(false);
                GC.Collect();
                GC.WaitForPendingFinalizers();
                GC.Collect();
                var afterMemory = GC.GetTotalMemory(false);
                var freed = beforeMemory - afterMemory;

                Log.Info("Garbage collection completed.");
                Log.Info($"Memory freed: {freed / 1024 / 1024} MB");
                Log.Info($"Current memory usage: {afterMemory / 1024 / 1024} MB");
            }
        }
    }

