Flask API for Sanity & Bingo App

This Flask application serves as a backend API, providing data from two separate MySQL databases: sanity2 and sanitybingo. It exposes various endpoints to retrieve game-related data, user information, and statistics for what appears to be a gaming community application.
Table of Contents

    Prerequisites

    Installation & Setup

    Running the Application

    API Endpoints

        Sanity API (/api/*)

        Bingo API (/api/bingo/*)

Running the Application

To run the Flask development server, use the following command:

flask run

By default, the API will be available at http://127.0.0.1:5000.
API Endpoints

The API is divided into two main sections based on the database they interact with.
Sanity API (/api/*)

These endpoints connect to the sanity2 database.
GET /api/rankChanges

Fetches a log of user rank changes.

    Public URL: https://sanityosrs.com/api/rankChanges

    Returns: A JSON array of objects with the following fields:

        actionDate: The timestamp of the rank change.

        userid: The unique ID of the user.

        displayName: The display name of the user.

        rank_before: The name of the rank before the change.

        rank_after: The name of the new rank.

        rankId_before: The ID of the rank before the change.

        rankId_after: The ID of the new rank.

GET /api/getUserEhb

Retrieves the total and categorized "Efficient Hours Billed" (EHB) for each user.

    Public URL: https://sanityosrs.com/api/getUserEhb

    Returns: A JSON array of objects with the following fields:

        displayName: The display name of the user.

        associated_rsns: A comma-separated string of the user's main and alt RSNs.

        total_weekly_ehb: The sum of all weekly EHB.

        Plus individual fields for weekly EHB from various bosses (e.g., chambers_of_xericWeeklyEHB, the_corrupted_gauntletWeeklyEHB, etc.)

GET /api/miscroles

Fetches miscellaneous roles assigned to users.

    Public URL: https://sanityosrs.com/api/miscroles

    Returns: A JSON array of objects with the following fields:

        roleName: The name of the miscellaneous role.

        displayName: The display name of the user assigned to the role.

GET /api/discordProfileUrl

Gets the Discord profile picture URL for users.

    Public URL: https://sanityosrs.com/api/discordProfileUrl

    Returns: A JSON array of objects with the following fields:

        displayName: The display name of the user.

        discordProfileImageUrl: The URL to the user's Discord profile image.

GET /api/getRSNkc

Fetches boss kill counts (kc) for each RuneScape Name (RSN).

    Public URL: https://sanityosrs.com/api/getRSNkc

    Returns: A JSON array of objects where each object represents an RSN and contains the following fields:

        RSN: The RuneScape Name of the player.

        A series of fields for each boss (e.g., abyssal_sire, alchemical_hydra, etc.) with their corresponding kill count.

GET /api/discordmsgssentyearly, ...monthly, ...weekly

Counts Discord messages sent by each user over the last year, month, or 7 days.

    Public URLs:

        https://sanityosrs.com/api/discordmsgssentyearly

        https://sanityosrs.com/api/discordmsgssentmonthly

        https://sanityosrs.com/api/discordmsgssent

    Returns: A JSON array of objects with the following fields:

        messageCount: The total number of messages sent in the period.

        displayName: The display name of the user.

GET /api/users

Fetches a detailed list of all active users.

    Public URL: https://sanityosrs.com/api/users

    Returns: A JSON array of objects with the following fields:

        displayName, points, rankId, rank_name, mainRSN, altRSN, joinDate, diaryPoints, masterDiaryPoints, flavourText, diaryTierClaimed, nationality, points_past_3_months, points_current_month_to_today, points_last_month, points_two_months_ago.

GET /api/diarytimes

Retrieves the required completion times for different diary tiers for various bosses.

    Public URL: https://sanityosrs.com/api/diarytimes

    Returns: A JSON array of objects with the following fields:

        name: The name of the boss.

        scale, maxDifficulty, timeEasy, timeMedium, timeHard, timeElite, timeMaster.

GET /api/approveddrops

Fetches statistics on approved drop submissions by reviewers over the last 12 months.

    Public URL: https://sanityosrs.com/api/approveddrops

    Returns: A JSON array of objects with the following fields:

        count(*): The number of submissions for that status and reviewer.

        displayName: The display name of the reviewer.

        name: The status of the submission (e.g., "Approved").

GET /api/bingowinners

Retrieves a list of past bingo winners.

    Public URL: https://sanityosrs.com/api/bingowinners

    Returns: A JSON array of objects with the following fields:

        bingoId: The ID of the bingo event.

        bingoName: The name of the bingo event.

        teamName: The name of the winning team.

        participants: A list of participants on the winning team.

GET /api/approvedpbs

Fetches statistics on approved Personal Best (PB) submissions by reviewers over the last 12 months.

    Public URL: https://sanityosrs.com/api/approvedpbs

    Returns: A JSON array of objects with the following fields:

        count(*): The number of PBs for that status and reviewer.

        displayName: The display name of the reviewer.

        name: The status of the submission (e.g., "Approved").

GET /api/points & GET /api/pointslimited

Retrieves a log of all points awarded. The limited version fetches the last 1000 records.

    Public URL (all): https://sanityosrs.com/api/points

    Public URL (limited): https://sanityosrs.com/api/pointslimited

    Returns: A JSON array of objects with the following fields:

        Id: The unique ID of the point entry.

        displayName: The user who received the points.

        points: The number of points awarded.

        notes: Notes about the point entry.

        messageUrl: A URL to the related submission message.

        date: The date the points were awarded.

GET /api/bossImages

Fetches the names and image URLs for all bosses.

    Public URL: https://sanityosrs.com/api/bossImages

    Returns: A JSON array of objects with name and imageUrl.

GET /api/drops & GET /api/dropslimited

Fetches a log of all drop submissions. The limited version fetches the last 1000 records.

    Public URL (all): https://sanityosrs.com/api/drops

    Public URL (limited): https://sanityosrs.com/api/dropslimited

    Returns: A JSON array of objects with the following fields:

        Id: The unique ID of the submission.

        submitter: The display name of the user who submitted the drop.

        member_names: Comma-separated list of participants.

        notes, value, status_name, imageUrl, reviewedDate, reviewer, bingo.

GET /api/personalbests & GET /api/personalbestslimited

Fetches a log of all approved personal best time submissions. The limited version fetches the last 1000 records.

    Public URL (all): https://sanityosrs.com/api/personalbests

    Public URL (limited): https://sanityosrs.com/api/personalbestslimited

    Returns: A JSON array of objects with the following fields:

        submissionId: The unique ID of the submission.

        member_names: Comma-separated list of participants.

        boss_name: The name of the boss.

        scale, time, imageUrl, submittedDate.

Bingo API (/api/bingo/*)

These endpoints connect to the sanitybingo database and are used for managing bingo events.
GET /api/bingo/drops

Fetches bingo-specific drop submissions.

    Public URL: https://sanityosrs.com/api/bingo/drops

    Returns: A JSON array of bingo drop objects with fields: Id, submitter, member_names, notes, value, status_name, imageUrl, reviewedDate, reviewer.

GET /api/bingo/teammembers

Fetches all bingo team members and their associated team ID.

    Public URL: https://sanityosrs.com/api/bingo/teammembers

    Returns: A JSON array of objects with fields: team_id, displayName, mainRSN, altRSN.

GET /api/bingo/board

Fetches all tiles for the currently active bingo board.

    Public URL: https://sanityosrs.com/api/bingo/board

    Returns: A JSON array of tile objects with fields: tile_id, text, sub_text, points, tileType, dropOrPointReq, image_url, completed.

GET /api/bingo/events

Fetches details of the currently active bingo event.

    Public URL: https://sanityosrs.com/api/bingo/events

    Returns: A JSON array of event objects with fields: id, name, start_date, end_date, is_active.

GET /api/bingo/raiditemvalues

Fetches the point values for specific raid items in the active bingo.

    Public URL: https://sanityosrs.com/api/bingo/raiditemvalues

    Returns: A JSON array of objects with fields: boss, item, points.

GET /api/bingo/bossehb

Fetches the EHB values for bosses in the active bingo.

    Public URL: https://sanityosrs.com/api/bingo/bossehb

    Returns: A JSON array of objects with fields: boss, ehb.

GET /api/bingo/tileitems

Fetches the specific items required for each tile in the bingo.

    Public URL: https://sanityosrs.com/api/bingo/tileitems

    Returns: A JSON array of objects with fields: id, eventId, dropName, tileId.

GET /api/bingo/teams

Fetches details for all registered bingo teams.

    Public URL: https://sanityosrs.com/api/bingo/teams

    Returns: A JSON array of team objects with fields: id, name, captain_userid, captain_name, cocaptain_userid, cocaptain_name.

GET /api/bingo/bossitems

Fetches a list of all possible boss items that can be used in the bingo generator.

    Public URL: https://sanityosrs.com/api/bingo/bossitems

    Returns: A JSON array of item objects with fields: id, bossName, item, itemPoints, droprate, hoursToGetDrop.

GET /api/bingo/overview

Fetches aggregated data for the bingo overview page.

    Public URL: https://sanityosrs.com/api/bingo/overview

    Returns: A single JSON object with the keys: top_individual_ehb, top_individual_points, board_completion_percentage, team_leaderboard. The team_leaderboard is an array of objects with team stats.

GET /api/bingo/board_details/<int:event_id>

Fetches all tiles and their associated items for a specific event's board.

    Public URL Example: https://sanityosrs.com/api/bingo/board_details/1

    Returns: A JSON array of tile objects with fields: id, position, task_name, description, tileType, dropOrPointReq, points, image_url, and items (which is an array of required drop names).

POST /api/bingo/create_event

Creates a new, empty bingo event. This is not a publicly accessible GET endpoint.

    Body: A JSON object with name, start_date, and end_date.

    Returns: A success message and the new event's ID.

POST /api/bingo/update_board

Updates an existing bingo board. This is a destructive operation and not a publicly accessible GET endpoint.

    Body: A JSON object containing the eventId and a tiles array.

    Returns: A success message.