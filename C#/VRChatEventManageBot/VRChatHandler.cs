
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using VRChat.API.Client;
using VRChat.API.Model;
using VRChat.API.Api;
using Discord.WebSocket;
using Discord.Interactions;
using Discord;
using LogExtentions;
using System.Net;
using System.Collections.Concurrent;

namespace VRChatEventManageBot
{
    public class CacheHandler
    {
        private static readonly string CacheFilePath = "usercache.json";
        private static Dictionary<string, CacheItem> CacheDict = LoadCache();

        public static void AddCache(string username, string password, string discordUserName, string authCookie, string twoFactorCookie)
        {
            var item = new CacheItem
            {
                Username = username,
                Password = password,
                DiscordUserName = discordUserName,
                AuthCookie = authCookie,
                TwoFactorCookie = twoFactorCookie
            };

            CacheDict[discordUserName] = item;
            SaveCache();
        }

        public static CacheItem? GetCache(string discordUserName)
        {
            CacheDict.TryGetValue(discordUserName, out var item);
            return item;
        }

        private static void SaveCache()
        {
            var json = System.Text.Json.JsonSerializer.Serialize(CacheDict, new System.Text.Json.JsonSerializerOptions
            {
                WriteIndented = true
            });
            System.IO.File.WriteAllText(CacheFilePath, json);
        }

        private static Dictionary<string, CacheItem> LoadCache()
        {
            if (!System.IO.File.Exists(CacheFilePath))
                return new Dictionary<string, CacheItem>();

            try
            {
                var json = System.IO.File.ReadAllText(CacheFilePath);
                return System.Text.Json.JsonSerializer.Deserialize<Dictionary<string, CacheItem>>(json)
                       ?? new Dictionary<string, CacheItem>();
            }
            catch
            {
                return new Dictionary<string, CacheItem>();
            }
        }
    }

    public class CacheItem
    {
        public string Username { get; set; } = string.Empty;
        public string Password { get; set; } = string.Empty;
        public string DiscordUserName { get; set; } = string.Empty;
        public string AuthCookie { get; set; } = string.Empty;
        public string TwoFactorCookie { get; set; } = string.Empty;
    }

    public class VRChatHandler
    {
        // 2FA待機中のユーザーを管理するための辞書
        private static readonly ConcurrentDictionary<ulong, PendingLogin> PendingLogins = new();

        private class PendingLogin
        {
            public string Username { get; set; } = string.Empty;
            public string Password { get; set; } = string.Empty;
            public string DiscordUserName { get; set; } = string.Empty;
            public AuthenticationApi AuthApi { get; set; } = null!;
            public ApiClient Client { get; set; } = null!;
            public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
        }

        public static async Task LoginVRChatAsync(string username, string password, string discordUserName, SocketInteractionContext context)
        {
            Configuration config = new Configuration();

            config.Username = username;
            config.Password = password;
            config.UserAgent = "VRchatEventManage/0.0.1" + discordUserName;

            ApiClient client = new ApiClient();
            AuthenticationApi authApi = new AuthenticationApi(client, client, config);

            try
            {
                // 初回ログイン試行
                ApiResponse<CurrentUser> currentUserResp = authApi.GetCurrentUserWithHttpInfo();

                if (RequiresEmail2FA(currentUserResp))
                {
                    // 2FA待機状態を保存
                    var pendingLogin = new PendingLogin
                    {
                        Username = username,
                        Password = password,
                        DiscordUserName = discordUserName,
                        AuthApi = authApi,
                        Client = client
                    };

                    PendingLogins[context.User.Id] = pendingLogin;

                    // 2FAモーダルを表示
                    await context.Interaction.RespondWithModalAsync<Email2FAModal>($"email2fa_modal");
                }
                else
                {
                    // 2FAが不要な場合は直接ログイン完了
                    CurrentUser currentUser = authApi.GetCurrentUser();
                    await context.Interaction.RespondAsync($"Logged in as {currentUser.DisplayName}", ephemeral: true);

                    // Cookieを保存
                    await SaveCookies(username, password, discordUserName);
                }
            }
            catch (ApiException ex)
            {
                Log.Error($"Login error: {ex.Message}");
                Log.Error($"Status Code: {ex.ErrorCode}");
                Log.Error(ex.ToString());

                await context.Interaction.RespondAsync($"Login failed: {ex.Message}", ephemeral: true);
            }
            catch (Exception ex)
            {
                Log.Error($"Unexpected error: {ex.Message}");
                await context.Interaction.RespondAsync("An unexpected error occurred during login.", ephemeral: true);
            }
        }

        
        public static async Task Handle2FAModalAsync(Email2FAModal modal, SocketInteraction interaction)
        {
            try
            {
                var userId = interaction.User.Id;

                // 待機中のログイン情報を取得
                if (!PendingLogins.TryRemove(userId, out var pendingLogin))
                {
                    await interaction.RespondAsync("2FA session expired. Please try logging in again.", ephemeral: true);
                    return;
                }

                // 5分以上経過していたらタイムアウト
                if (DateTime.UtcNow - pendingLogin.CreatedAt > TimeSpan.FromMinutes(5))
                {
                    await interaction.RespondAsync("2FA session expired. Please try logging in again.", ephemeral: true);
                    return;
                }

                if (string.IsNullOrEmpty(modal.Email2FACode))
                {
                    await interaction.RespondAsync("2FA code cannot be empty.", ephemeral: true);
                    return;
                }

                Log.Info($"Attempting 2FA verification for user {pendingLogin.DiscordUserName} with code: {modal.Email2FACode}");

                // 2FAコードを送信
                pendingLogin.AuthApi.Verify2FAEmailCode(new TwoFactorEmailCode(modal.Email2FACode));
                CurrentUser currentUser = pendingLogin.AuthApi.GetCurrentUser();

                await interaction.RespondAsync($"Successfully logged in as {currentUser.DisplayName}", ephemeral: true);

                // Cookieを保存
                SaveCookies(pendingLogin.Username, pendingLogin.Password, pendingLogin.DiscordUserName);
            }
            catch (ApiException ex)
            {
                Log.Error($"2FA verification failed: {ex.Message}");
                Log.Error($"Error code: {ex.ErrorCode}");


                string errorMessage = ex.ErrorCode switch
                {
                    400 => "Invalid 2FA code. Please check the code and try again.",
                    401 => "Authentication failed. Please login again.",
                    429 => "Too many attempts. Please wait a moment before trying again.",
                    _ => $"2FA verification failed: {ex.Message}"
                };

                await interaction.RespondAsync(errorMessage, ephemeral: true);
            }
            catch (Exception ex)
            {
                Log.Error($"Unexpected error during 2FA: {ex}");
                await interaction.RespondAsync("An unexpected error occurred during 2FA verification. Please try logging in again.", ephemeral: true);
            }
        }

        private static async Task SaveCookies(string username, string password, string discordUserName)
        {
            try
            {
                // Cookieを抽出してキャッシュに保存
                var cookies = ApiClient.CookieContainer.GetAllCookies();
                Log.Info($"Extracted {cookies.Count} cookies for user {discordUserName}");
                foreach ( var cookie in cookies ) {
                    Log.Info($"Cookie: {cookie}");
                }
                string authCookie = cookies.FirstOrDefault(x => x.Name == "auth")?.Value ?? "";
                string twoFactorCookie = cookies.FirstOrDefault(x => x.Name == "twoFactorAuth")?.Value ?? "";

                CacheHandler.AddCache(username, password, discordUserName, authCookie, twoFactorCookie);
                Log.Info($"Cookies saved for user: {discordUserName}");
            }
            catch (Exception ex)
            {
                Log.Error($"Failed to save cookies: {ex.Message}");
            }
        }

        private static bool RequiresEmail2FA(ApiResponse<CurrentUser> resp)
        {
            return resp.RawContent.Contains("emailOtp");
        }

        // 定期的にタイムアウトした待機中のログインをクリーンアップ
        public static void CleanupExpiredLogins()
        {
            var expiredKeys = PendingLogins
                .Where(kvp => DateTime.UtcNow - kvp.Value.CreatedAt > TimeSpan.FromMinutes(5))
                .Select(kvp => kvp.Key)
                .ToList();

            foreach (var key in expiredKeys)
            {
                PendingLogins.TryRemove(key, out _);
            }
        }
        // VRChatHandler.cs

        public static async Task PostCalendar(string title, string description, CreateCalendarEventRequest.AccessTypeEnum visuability, DateTime startTime, List<string> platforms,DateTime endTime, bool sentNotification, string groupId, string discordUserId, SocketInteraction interaction, string category)
        {
            var cache = CacheHandler.GetCache(discordUserId);
            if (cache == null || string.IsNullOrEmpty(cache.AuthCookie))
            {
                await interaction.RespondAsync("ログインしていません。`/login`コマンドで先にログインしてください。", ephemeral: true);
                return;
            }

            try
            {
                var config = new Configuration();
                var cookieHeader = $"auth={cache.AuthCookie};";
                if (!string.IsNullOrEmpty(cache.TwoFactorCookie))
                {
                    cookieHeader += $" twoFactorAuth={cache.TwoFactorCookie};";
                }
                config.DefaultHeaders.Add("Cookie", cookieHeader);
                config.UserAgent = "VRchatEventManage/0.0.1 " + discordUserId;

                var client = new ApiClient();
                var authApi = new AuthenticationApi(client, client, config);
                var calendarApi = new CalendarApi(client, client, config);
                var groupsApi = new GroupsApi(client, client, config);

                try
                {
                    CurrentUser currentUser = await authApi.GetCurrentUserAsync();
                    Log.Info($"ユーザー: {currentUser.DisplayName} としてCookieでの認証に成功しました。");
                }
                catch (ApiException authEx) when (authEx.ErrorCode == 401)
                {
                    Log.Warn($"ユーザーID: {discordUserId} のCookieが無効です。再ログインが必要です。");
                    await interaction.RespondAsync("VRChatのセッションが切れました。`/login`コマンドで再度ログインしてください。", ephemeral: true);
                    return;
                }

                var group = await groupsApi.GetGroupAsync(groupId);

                // --- ★★★ 修正箇所 ★★★ ---
                // APIの仕様に合わせたリクエストオブジェクトを作成します。
                var calendarRequest = new CreateCalendarEventRequest(
                    title: title, // プロパティ名が 'title' ではなく 'name' の可能性が高いです
                    description: description,
                    category: category,                  // 引数で受け取ったカテゴリを使用
                    startsAt: startTime.ToUniversalTime(), // UTCに変換して送信
                    endsAt: endTime.ToUniversalTime(),     // UTCに変換して送信
                    platforms: platforms,                // 引数で受け取ったプラットフォームリストを使用
                    sendCreationNotification: sentNotification,
                    accessType: visuability // 'group' または 'public' を指定 (今回はグループイベントなので 'Group')
                );

                var createdCalendar = await calendarApi.CreateGroupCalendarEventAsync(groupId, calendarRequest);

                Log.Info($"グループ '{group.Name}' にカレンダーイベント '{title}' を作成しました。");
                await interaction.FollowupAsync($"グループ '{group.Name}' にカレンダーイベントを作成しました！\nタイトル: '{title}'", ephemeral: true);
            }
            catch (ApiException apiEx)
            {
                Log.Error($"VRChat APIエラー (カレンダーイベント作成時): {apiEx.Message}");
                Log.Error($"ステータスコード: {apiEx.ErrorCode}");
                string errorMessage = apiEx.ErrorCode switch
                {
                    401 => "認証に失敗しました。再度ログインしてください。",
                    403 => "このグループにカレンダーイベントを作成する権限がありません。",
                    404 => "指定されたグループが見つかりませんでした。設定を確認してください。",
                    _ => $"APIエラーが発生しました: {apiEx.Message}"
                };
                await interaction.FollowupAsync(errorMessage, ephemeral: true);
            }
            catch (Exception ex)
            {
                Log.Error($"予期せぬエラー (カレンダーイベント作成時): {ex.Message}");
                await interaction.FollowupAsync("カレンダーイベント作成中に予期せぬエラーが発生しました。", ephemeral: true);
            }
        }
        public enum EventCategory
        {
            Event,
            Meeting,
            Party,

            Other
        }



        public static async Task PostContents(string title,string contents, bool sendnotification, VRChatPostType contentsType, string groupId, string discordUserId, SocketInteraction interaction)
        {
            var cache = CacheHandler.GetCache(discordUserId);
            if (cache == null || string.IsNullOrEmpty(cache.AuthCookie))
            {
                await interaction.FollowupAsync("ログインしていません。`/login`コマンドで先にログインしてください。", ephemeral: true);
                return;
            }


            try
            {

                var config = new Configuration();

                var cookieHeader = $"auth={cache.AuthCookie};";
                if (!string.IsNullOrEmpty(cache.TwoFactorCookie))
                {
                    cookieHeader += $" twoFactorAuth={cache.TwoFactorCookie};";
                }
                config.DefaultHeaders.Add("Cookie", cookieHeader);


                config.UserAgent = "VRchatEventManage/0.0.1 " + discordUserId;

                var client = new ApiClient();


                var authApi = new AuthenticationApi(client, client, config);
                var groupsApi = new GroupsApi(client, client, config);



                try
                {
                    CurrentUser currentUser = await authApi.GetCurrentUserAsync();
                    Log.Info($"ユーザー: {currentUser.DisplayName} としてCookieでの認証に成功しました。");
                }
                catch (ApiException authEx) when (authEx.ErrorCode == 401) // 401 Unauthorized
                {
                    Log.Warn($"ユーザーID: {discordUserId} のCookieが無効です。再ログインが必要です。");
                    await interaction.FollowupAsync("VRChatのセッションが切れました。`/login`コマンドで再度ログインしてください。", ephemeral: true);
                    return;
                }
                var group = await groupsApi.GetGroupAsync(groupId);
                if (contentsType == VRChatPostType.Post)
                {

                    // 5. 投稿リクエストを作成
                    var postRequest = new CreateGroupPostRequest(
                        title: title,
                        text: contents,
                        visibility: GroupPostVisibility.Group, 
                      
                        sendNotification: true // グループメンバーに通知を送信
                    );

                    // 6. GroupsApiで投稿を実行
                    var createdPost = await groupsApi.AddGroupPostAsync(groupId,postRequest);
                    
                    Log.Info($"グループ {(group.Name)} に投稿 '{createdPost.Title}' を作成しました。");

                    // 7. 成功をDiscordに通知
                    await interaction.FollowupAsync($"グループ{(groupsApi.GetGroup(groupId).Name)}に投稿しました！\nタイトル: '{createdPost.Title}'", ephemeral: true);
                }
                else
                {
                    var postRequest = new CreateGroupAnnouncementRequest(
                        title: title,
                        text: contents,
                        sendNotification: true 
                    );
                    var createdAnnouncement = await groupsApi.CreateGroupAnnouncementAsync(groupId, postRequest);
                    
                    Log.Info($"グループ {group.Name} にアナウンス '{createdAnnouncement.Title}' を作成しました。");
                    await interaction.FollowupAsync($"グループ{(groupsApi.GetGroup(groupId).Name)}にアナウンスを作成しました！\nタイトル: '{createdAnnouncement.Title}'", ephemeral: true);

                }
            }
            catch (ApiException apiEx)
            {
                Log.Error($"VRChat APIエラー (投稿作成時): {apiEx.Message}");
                Log.Error($"ステータスコード: {apiEx.ErrorCode}");

                string errorMessage = apiEx.ErrorCode switch
                {
                    401 => "認証に失敗しました。再度ログインしてください。",
                    403 => "このグループに投稿する権限がありません。",
                    404 => "指定されたグループが見つかりませんでした。設定を確認してください。",
                    _ => $"APIエラーが発生しました: {apiEx.Message}"
                };
                await interaction.FollowupAsync(errorMessage, ephemeral: true);
            }
            catch (Exception ex)
            {
                Log.Error($"予期せぬエラー (投稿作成時): {ex.Message}");
                await interaction.FollowupAsync("投稿中に予期せぬエラーが発生しました。", ephemeral: true);
            }
        }
        public enum VRChatPostType
        {
            Post,
            Announcement,
            Other
        }
    }
    public class Email2FAModal : IModal
    {
        public string Title => "Email 2FA Required";

        [InputLabel("Enter the 6-digit code sent to your email:")]
        [RequiredInput(true)]
        [ModalTextInput("email2fa_code", TextInputStyle.Short, "123456", 6, 6)]
        public string Email2FACode { get; set; } = string.Empty;
    }
}