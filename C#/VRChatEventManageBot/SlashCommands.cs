using Discord.Commands;
using Discord.Interactions;
using Discord.WebSocket;
using LogExtentions;
using VRChat.API.Model;
using VRChatEventManageBot;

namespace Discord.commands
{
    [Discord.Interactions.RequireContext(Discord.Interactions.ContextType.Guild)]
    public class VRChatCommand : InteractionModuleBase<SocketInteractionContext>
    {
        public InteractionService Commands { get; set; } = null!;

        [SlashCommand("login", "Login to VRChat")]
        public async Task LoginAsync(
            [Discord.Interactions.Summary("username", "Your VRChat username")] string username,
            [Discord.Interactions.Summary("password", "Your VRChat password")] string password)
        {
            // 入力値検証
            if (string.IsNullOrWhiteSpace(username) || string.IsNullOrWhiteSpace(password))
            {
                await FollowupAsync("Username and password cannot be empty.", ephemeral: true);
                return;
            }



            await VRChatEventManageBot.VRChatHandler.LoginVRChatAsync(username, password, Context.User.Username, Context);
        }
        [SlashCommand("postcontent", "VRChatグループに投稿またはアナウンスを作成します。")]
        public async Task PostContentAsync(
    [Interactions.Summary("groupid", "投稿先のグループID (例: grp_...)")] string groupId,
    [Interactions.Summary("title", "投稿のタイトル")] string title,
    [Interactions.Summary("message", "投稿の本文")] string message,
    [Interactions.Summary("contentstype", "投稿の種類を選択してください")][Choice("通常投稿 (Post)", 1)][Choice("アナウンス (Announcement)", 2)] int contentsTypeChoice,
    [Interactions.Summary("notification", "メンバーに通知を送信する")]bool isSentNotification)
        {
            await DeferAsync();
            // --- 1. 入力値の検証 ---
            if (string.IsNullOrWhiteSpace(groupId) || string.IsNullOrWhiteSpace(title) || string.IsNullOrWhiteSpace(message))
            {
                await FollowupAsync("Group ID, Title, Message のすべてを入力してください。", ephemeral: true);
                return;
            }

            // --- 2. Discordコマンドの選択肢(int)をプログラム用のenum型に変換 ---
            var postType = contentsTypeChoice switch
            {
                1 => VRChatEventManageBot.VRChatHandler.VRChatPostType.Post,
                2 => VRChatEventManageBot.VRChatHandler.VRChatPostType.Announcement,
                // DiscordのUI制約により、通常はこのパスに到達しない
                _ => VRChatEventManageBot.VRChatHandler.VRChatPostType.Other
            };

            if (postType == VRChatEventManageBot.VRChatHandler.VRChatPostType.Other)
            {
                await FollowupAsync("無効な投稿タイプが選択されました。", ephemeral: true);
                return;
            }

            // --- 3. VRChatHandlerのメソッドを呼び出す ---
            // この後の処理（VRChat APIとの通信とDiscordへの返信）はすべてPostContentsメソッドが担当します。
            await VRChatEventManageBot.VRChatHandler.PostContents(
                title: title,
                contents: message,
                contentsType: postType,
                sendnotification: isSentNotification,
                groupId: groupId,
                discordUserId: Context.User.Username, // CacheHandlerでキーとして使用
                interaction: Context.Interaction      // Discordへの返信に使用
            );
        }

        // Discordのコマンドハンドラークラス内

        [SlashCommand("createcalendar", "VRChatグループにカレンダーイベントを作成します。")]
        public async Task CreateCalendarEventAsync(
    [Interactions.Summary("groupid", "イベントを作成するグループID (例: grp_...)")] string groupId,
    [Interactions.Summary("name", "イベントのタイトル")] string eventName,
    [Interactions.Summary("description", "イベントの説明")] string description,
    [Interactions.Summary("starttime", "イベントの開始日時 (例: 2025-09-05 21:00)")] string startTime,
    [Interactions.Summary("endtime", "イベントの終了日時 (例: 2025-09-05 22:00)")] string endTime,

    // --- ★★★ 追加箇所 ★★★ ---
    [Interactions.Summary("category", "イベントのカテゴリを選択")]
    [Choice("音楽 (Music)", "music")]
    [Choice("ゲーム (Gaming)", "gaming")]
    [Choice("雑談 (Hangout)", "hangout")]
    [Choice("ロールプレイ (Roleplaying)", "roleplaying")]
    [Choice("探索 (Exploration)", "exploration")]
    [Choice("映画＆メディア (Film & Media)", "film_media")]
    [Choice("アート (Arts)", "arts")]
    [Choice("教育 (Education)", "education")]
    [Choice("パフォーマンス (Performance)", "performance")]
    [Choice("その他 (Other)", "other")]
    string category,

    [Interactions.Summary("platforms", "対応プラットフォーム")]
    [Choice("PC & Quest", "all")]
    [Choice("PCのみ", "pc")]
    [Choice("Questのみ", "quest")]
    string platformChoice,

    [Interactions.Summary("sendnotification", "作成時に通知を送るか")] bool sentNotification,
    [Interactions.Summary("visuability","公開先")]
    [Choice("グループのみ","group")]
    [Choice("全体公開","public")]
string visuability = "group"
        )
        {
            await DeferAsync();
            // --- 1. 入力値の検証 ---
            if (string.IsNullOrWhiteSpace(groupId) || string.IsNullOrWhiteSpace(eventName) ||
                string.IsNullOrWhiteSpace(description) || string.IsNullOrWhiteSpace(startTime) ||
                string.IsNullOrWhiteSpace(endTime))
            {
                await FollowupAsync("すべてのフィールドを入力してください。", ephemeral: true);
                return;
            }
            // 日本時間(JST)として日時を解釈するように設定
            if (!DateTime.TryParse(startTime, out DateTime parsedStartTime) ||
                !DateTime.TryParse(endTime, out DateTime parsedEndTime))
            {
                await FollowupAsync("日時は `2025-09-05 21:00` のような形式で入力してください。", ephemeral: true);
                return;
            }
            if (parsedEndTime <= parsedStartTime)
            {
                await FollowupAsync("終了日時は開始日時より後でなければなりません。", ephemeral: true);
                return;
            }

            // --- ★★★ 追加箇所 ★★★ ---
            // プラットフォームの選択肢をAPI用のリストに変換
            List<string> platforms = platformChoice switch
            {
                "pc" => new List<string> { "standalonewindows" },
                "quest" => new List<string> { "android" },
                _ => new List<string> { "standalonewindows", "android" } // "all" の場合
            };
            // --- ★★★ 追加箇所 ★★★ ---
            CreateCalendarEventRequest.AccessTypeEnum accessTypeEnum;
            switch (visuability)
            {
                case "group":
                    accessTypeEnum = CreateCalendarEventRequest.AccessTypeEnum.Group;
                    break;
                case "public":
                    accessTypeEnum = CreateCalendarEventRequest.AccessTypeEnum.Public;
                    break;
                default:
                    accessTypeEnum = CreateCalendarEventRequest.AccessTypeEnum.Group; // デフォルト値
                    break;
            }

            // --- 2. VRChatHandlerのメソッドを呼び出す ---
            await VRChatEventManageBot.VRChatHandler.PostCalendar(
                title: eventName,
                description: description,
                startTime: parsedStartTime, // 時刻はPostCalendar側でUTCに変換
                endTime: parsedEndTime,
                sentNotification: sentNotification,
                groupId: groupId,
                visuability:accessTypeEnum, 
                discordUserId: Context.User.Username,
                interaction: Context.Interaction,
                category: category,         // 追加
                platforms: platforms        // 追加
            );
        }
        [ModalInteraction("email2fa_modal")]
        public async Task Handle2FAModalAsync(Email2FAModal modal)
        {
            Log.Info(Context.User.Username +$"2FAコード: {modal.Email2FACode}");
            await VRChatEventManageBot.VRChatHandler.Handle2FAModalAsync(modal, Context.Interaction);
        }


    }

}
