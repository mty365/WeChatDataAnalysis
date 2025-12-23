<template>
  <div class="h-screen flex overflow-hidden" style="background-color: #EDEDED">
    <!-- 左侧边栏 -->
    <div class="w-16 border-r border-gray-200 flex flex-col" style="background-color: #e8e7e7">
      <div class="flex-1 flex flex-col justify-start pt-0">
        <!-- 聊天图标 (与 oh-my-wechat 一致) -->
        <div class="w-16 h-16 flex items-center justify-center chat-tab selected text-[#07b75b]">
          <div class="w-7 h-7">
            <svg class="w-full h-full" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M12 19.8C17.52 19.8 22 15.99 22 11.3C22 6.6 17.52 2.8 12 2.8C6.48 2.8 2 6.6 2 11.3C2 13.29 2.8 15.12 4.15 16.57C4.6 17.05 4.82 17.29 4.92 17.44C5.14 17.79 5.21 17.99 5.23 18.4C5.24 18.59 5.22 18.81 5.16 19.26C5.1 19.75 5.07 19.99 5.13 20.16C5.23 20.49 5.53 20.71 5.87 20.72C6.04 20.72 6.27 20.63 6.72 20.43L8.07 19.86C8.43 19.71 8.61 19.63 8.77 19.59C8.95 19.55 9.04 19.54 9.22 19.54C9.39 19.53 9.64 19.57 10.14 19.65C10.74 19.75 11.37 19.8 12 19.8Z"/>
            </svg>
          </div>
        </div>
        
        <!-- 隐私模式按钮 -->
        <div
          class="w-16 h-12 flex items-center justify-center cursor-pointer transition-colors"
          :class="privacyMode ? 'text-[#03C160]' : 'text-gray-500 hover:text-gray-700'"
          @click="privacyMode = !privacyMode"
          :title="privacyMode ? '关闭隐私模式' : '开启隐私模式'"
        >
          <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path v-if="privacyMode" stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
            <path v-else stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
            <circle v-if="!privacyMode" cx="12" cy="12" r="3" />
          </svg>
        </div>
      </div>
    </div>

    <!-- 中间列表区域 -->
    <div class="w-80 border-r border-gray-200 flex flex-col min-h-0" style="background-color: #F7F7F7">
      <!-- 聊天列表 -->
      <div class="h-full flex flex-col min-h-0">
        <!-- 搜索栏 -->
        <div class="h-16 p-4 border-b border-gray-200" style="background-color: #F7F7F7">
          <div class="flex items-center space-x-2">
            <div class="relative flex-1">
              <input
                type="text"
                placeholder="搜索"
                v-model="searchQuery"
                class="w-full pl-8 pr-4 py-2 text-sm focus:outline-none rounded-md"
                style="background-color: #EAEAEA; border: none;"
              >
              <svg class="w-4 h-4 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 16 16">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7.33333 12.6667C10.2789 12.6667 12.6667 10.2789 12.6667 7.33333C12.6667 4.38781 10.2789 2 7.33333 2C4.38781 2 2 4.38781 2 7.33333C2 10.2789 4.38781 12.6667 7.33333 12.6667Z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M14 14L11.1 11.1" />
              </svg>
            </div>

            <select
              v-if="availableAccounts.length > 1"
              v-model="selectedAccount"
              @change="onAccountChange"
              class="text-xs px-2 py-2 rounded-md border border-gray-200 focus:outline-none"
              style="background-color: #EAEAEA;"
            >
              <option v-for="acc in availableAccounts" :key="acc" :value="acc">{{ acc }}</option>
            </select>
          </div>
        </div>

        <!-- 联系人列表 -->
        <div class="flex-1 overflow-y-auto min-h-0">
          <div v-if="isLoadingContacts" class="px-3 py-2 text-sm text-gray-500">
            加载中...
          </div>
          <div v-else-if="contactsError" class="px-3 py-2 text-sm text-red-500 whitespace-pre-wrap">
            {{ contactsError }}
          </div>
          <div v-else-if="contacts.length === 0" class="px-3 py-2 text-sm text-gray-500">
            暂无会话
          </div>
          <template v-else>
            <div v-for="contact in filteredContacts" :key="contact.id"
              class="px-3 py-2 cursor-pointer transition-colors duration-150 border-b border-gray-100"
              :class="selectedContact?.id === contact.id ? 'bg-[#DEDEDE] hover:bg-[#d3d3d3]' : 'hover:bg-[#eaeaea]'"
              @click="selectContact(contact)">
              <div class="flex items-center space-x-3">
                <!-- 联系人头像 -->
                <div class="w-10 h-10 rounded-md overflow-hidden bg-gray-300 flex-shrink-0" :class="{ 'privacy-blur': privacyMode }">
                  <div v-if="contact.avatar" class="w-full h-full">
                    <img :src="contact.avatar" :alt="contact.name" class="w-full h-full object-cover">
                  </div>
                  <div v-else class="w-full h-full flex items-center justify-center text-white text-xs font-bold"
                    :style="{ backgroundColor: contact.avatarColor || '#4B5563' }">
                    {{ contact.name.charAt(0) }}
                  </div>
                </div>
                
                <!-- 联系人信息 -->
                <div class="flex-1 min-w-0">
                  <div class="flex items-center justify-between">
                    <h3 class="text-sm font-medium text-gray-900 truncate" :class="{ 'privacy-blur': privacyMode }">{{ contact.name }}</h3>
                    <div class="flex items-center flex-shrink-0 ml-2">
                      <span v-if="contact.unreadCount > 0" class="text-[10px] text-white bg-red-500 rounded-full min-w-[18px] h-[18px] px-1 flex items-center justify-center mr-2">
                        {{ contact.unreadCount > 99 ? '99+' : contact.unreadCount }}
                      </span>
                      <span class="text-xs text-gray-500">{{ contact.lastMessageTime }}</span>
                    </div>
                  </div>
                  <p class="text-xs text-gray-500 truncate mt-0.5 leading-tight" :class="{ 'privacy-blur': privacyMode }">{{ contact.lastMessage }}</p>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- 样式展示列表已移除 -->
    </div>

    <!-- 右侧聊天区域 -->
    <div class="flex-1 flex flex-col min-h-0" style="background-color: #EDEDED">
      <div v-if="selectedContact" class="flex-1 flex flex-col min-h-0">
        <!-- 聊天头部 -->
        <div class="h-16 px-6 flex items-center" style="background-color: #EDEDED; border-bottom: 1px solid #d5d5d5;">
          <div class="flex items-center space-x-3">
            <h2 class="text-lg font-medium text-gray-900" :class="{ 'privacy-blur': privacyMode }">
              {{ selectedContact ? selectedContact.name : '' }}
            </h2>
          </div>
          <div class="ml-auto flex items-center space-x-2">
            <button
              class="text-xs px-3 py-1 rounded-md bg-white border border-gray-200 hover:bg-gray-50"
              @click="refreshSelectedMessages"
              :disabled="isLoadingMessages"
            >
              刷新
            </button>
            <button
              class="text-xs px-3 py-1 rounded-md bg-white border border-gray-200 hover:bg-gray-50"
              @click="openExportModal"
              :disabled="isExportCreating"
            >
              导出
            </button>
          </div>
        </div>

        <!-- 聊天消息区域 -->
        <div ref="messageContainerRef" class="flex-1 overflow-y-auto p-4 min-h-0" @scroll="onMessageScroll">
          <div v-if="selectedContact && hasMoreMessages" class="flex justify-center mb-4">
            <div
              class="text-xs px-3 py-1 rounded-md bg-white border border-gray-200 text-gray-700 select-none"
              :class="isLoadingMessages ? 'opacity-60' : 'hover:bg-gray-50 cursor-pointer'"
              @click="!isLoadingMessages && loadMoreMessages()"
            >
              {{ isLoadingMessages ? '加载中...' : '继续上滑加载更多' }}
            </div>
          </div>

          <div v-if="isLoadingMessages && messages.length === 0" class="text-center text-sm text-gray-500 py-6">
            加载中...
          </div>
          <div v-else-if="messagesError" class="text-center text-sm text-red-500 py-6 whitespace-pre-wrap">
            {{ messagesError }}
          </div>
          <div v-else-if="messages.length === 0" class="text-center text-sm text-gray-500 py-6">
            暂无聊天记录
          </div>

          <div v-for="message in renderMessages" :key="message.id" class="mb-6">
            <div v-if="message.showTimeDivider" class="flex justify-center mb-4">
              <div class="px-3 py-1 text-xs text-[#9e9e9e]">
                {{ message.timeDivider }}
              </div>
            </div>

            <div v-if="message.renderType === 'system'" class="flex justify-center">
              <div class="px-3 py-1 text-xs text-[#9e9e9e]">
                {{ message.content }}
              </div>
            </div>

            <div v-else class="flex items-center" :class="message.isSent ? 'justify-end' : 'justify-start'">
              <div class="flex items-start max-w-md" :class="message.isSent ? 'flex-row-reverse' : ''">
                <!-- 消息发送者头像 -->
                <div class="w-[36px] h-[36px] rounded-md overflow-hidden bg-gray-300 flex-shrink-0" :class="[message.isSent ? 'ml-3' : 'mr-3', { 'privacy-blur': privacyMode }]">
                  <div v-if="message.avatar" class="w-full h-full">
                    <img :src="message.avatar" :alt="message.sender + '的头像'" class="w-full h-full object-cover">
                  </div>
                  <div v-else class="w-full h-full flex items-center justify-center text-white text-xs font-bold"
                    :style="{ backgroundColor: message.avatarColor || (message.isSent ? '#4B5563' : '#6B7280') }">
                    {{ message.sender.charAt(0) }}
                  </div>
                </div>
                
                <!-- 消息内容气泡（精简：移除了专用消息组件） -->
                <div class="flex flex-col relative group" :class="[message.isSent ? 'items-end' : 'items-start', { 'privacy-blur': privacyMode }]">
                  <div v-if="message.isGroup && !message.isSent && message.senderDisplayName" class="text-[11px] text-gray-500 mb-1" :class="message.isSent ? 'text-right' : 'text-left'">
                    {{ message.senderDisplayName }}
                  </div>
                  <div
                    class="absolute -top-6 z-10 rounded bg-black/70 text-white text-[10px] px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap"
                    :class="message.isSent ? 'right-0' : 'left-0'"
                  >
                    {{ message.fullTime }}
                  </div>
                  <!-- 链接消息仍使用 LinkCard -->
                  <LinkCard
                    v-if="message.renderType === 'link'"
                    :href="message.url"
                    :heading="message.title || message.content"
                    :abstract="message.content"
                    :preview="message.preview"
                    :from="message.from"
                  />
                  <div v-else-if="message.renderType === 'file'"
                    class="wechat-redpacket-card wechat-special-card wechat-file-card msg-radius"
                    :class="message.isSent ? 'wechat-special-sent-side' : ''"
                    @click="onFileClick(message)"
                    @contextmenu="openMediaContextMenu($event, message, 'file')">
                    <div class="wechat-redpacket-content">
                      <div class="wechat-redpacket-info wechat-file-info">
                        <span class="wechat-file-name">{{ message.title || message.content || '文件' }}</span>
                        <span class="wechat-file-size" v-if="message.fileSize">{{ formatFileSize(message.fileSize) }}</span>
                      </div>
                      <img :src="getFileIconUrl(message.title)" alt="" class="wechat-file-icon" />
                    </div>
                    <div class="wechat-redpacket-bottom wechat-file-bottom">
                      <img :src="wechatPcLogoUrl" alt="" class="wechat-file-logo" />
                      <span>微信电脑版</span>
                    </div>
                  </div>
                  <div v-else-if="message.renderType === 'image'"
                    class="max-w-sm">
                    <div class="msg-radius overflow-hidden cursor-pointer" :class="message.isSent ? '' : ''" @click="message.imageUrl && openImagePreview(message.imageUrl)" @contextmenu="openMediaContextMenu($event, message, 'image')">
                      <img v-if="message.imageUrl" :src="message.imageUrl" alt="图片" class="max-w-[240px] max-h-[240px] object-cover hover:opacity-90 transition-opacity">
                      <div v-else class="px-3 py-2 text-sm max-w-sm relative msg-bubble whitespace-pre-wrap break-words leading-relaxed"
                        :class="message.isSent ? 'bg-[#95EC69] text-black bubble-tail-r' : 'bg-white text-gray-800 bubble-tail-l'">
                        {{ message.content }}
                      </div>
                    </div>
                  </div>
                  <div v-else-if="message.renderType === 'video'" class="max-w-sm">
                    <div class="msg-radius overflow-hidden relative bg-black/5" @contextmenu="openMediaContextMenu($event, message, 'video')">
                      <img v-if="message.videoThumbUrl" :src="message.videoThumbUrl" alt="视频" class="max-w-[260px] max-h-[260px] object-cover">
                      <div v-else class="px-3 py-2 text-sm relative msg-bubble whitespace-pre-wrap break-words leading-relaxed"
                        :class="message.isSent ? 'bg-[#95EC69] text-black bubble-tail-r' : 'bg-white text-gray-800 bubble-tail-l'">
                        {{ message.content }}
                      </div>
                      <a
                        v-if="message.videoThumbUrl && message.videoUrl"
                        :href="message.videoUrl"
                        target="_blank"
                        rel="noreferrer"
                        class="absolute inset-0 flex items-center justify-center"
                      >
                        <div class="w-12 h-12 rounded-full bg-black/45 flex items-center justify-center">
                          <svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                        </div>
                      </a>
                      <div class="absolute inset-0 flex items-center justify-center" v-else-if="message.videoThumbUrl">
                        <div class="w-12 h-12 rounded-full bg-black/45 flex items-center justify-center">
                          <svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div v-else-if="message.renderType === 'voice'"
                    class="wechat-voice-wrapper"
                    @contextmenu="openMediaContextMenu($event, message, 'voice')">
                    <div
                      class="wechat-voice-bubble msg-radius"
                      :class="message.isSent ? 'wechat-voice-sent' : 'wechat-voice-received'"
                      :style="{ width: getVoiceWidth(message.voiceDuration) }"
                      @click="message.voiceUrl && playVoice(message)"
                    >
                      <div class="wechat-voice-content" :class="message.isSent ? 'flex-row-reverse' : ''">
                        <svg class="wechat-voice-icon" :class="[message.isSent ? 'voice-icon-sent' : 'voice-icon-received', { 'voice-playing': playingVoiceId === message.id }]" viewBox="0 0 32 32" fill="currentColor">
                          <path d="M10.24 11.616l-4.224 4.192 4.224 4.192c1.088-1.056 1.76-2.56 1.76-4.192s-0.672-3.136-1.76-4.192z"></path>
                          <path class="voice-wave-2" d="M15.199 6.721l-1.791 1.76c1.856 1.888 3.008 4.48 3.008 7.328s-1.152 5.44-3.008 7.328l1.791 1.76c2.336-2.304 3.809-5.536 3.809-9.088s-1.473-6.784-3.809-9.088z"></path>
                          <path class="voice-wave-3" d="M20.129 1.793l-1.762 1.76c3.104 3.168 5.025 7.488 5.025 12.256s-1.921 9.088-5.025 12.256l1.762 1.76c3.648-3.616 5.887-8.544 5.887-14.016s-2.239-10.432-5.887-14.016z"></path>
                        </svg>
                        <span class="wechat-voice-duration">{{ getVoiceDurationInSeconds(message.voiceDuration) }}"</span>
                      </div>
                      <span v-if="!message.voiceRead && !message.isSent" class="wechat-voice-unread"></span>
                    </div>
                    <audio
                      v-if="message.voiceUrl"
                      :ref="el => setVoiceRef(message.id, el)"
                      :src="message.voiceUrl"
                      preload="none"
                      class="hidden"
                    ></audio>
                  </div>
                  <div v-else-if="message.renderType === 'voip'"
                    class="wechat-voip-bubble msg-radius"
                    :class="message.isSent ? 'wechat-voip-sent' : 'wechat-voip-received'">
                    <div class="wechat-voip-content" :class="message.isSent ? 'flex-row-reverse' : ''">
                      <img v-if="message.voipType === 'video'" src="/assets/images/wechat/wechat-video-light.png" class="wechat-voip-icon" alt="">
                      <img v-else src="/assets/images/wechat/wechat-audio-light.png" class="wechat-voip-icon" alt="">
                      <span class="wechat-voip-text">{{ message.content || '通话' }}</span>
                    </div>
                  </div>
                  <div v-else-if="message.renderType === 'emoji'" class="max-w-sm flex items-center group">
                    <template v-if="message.emojiUrl">
                      <img :src="message.emojiUrl" alt="表情" class="w-24 h-24 object-contain" @contextmenu="openMediaContextMenu($event, message, 'emoji')">
                      <button
                        v-if="shouldShowEmojiDownload(message)"
                        class="ml-2 text-xs px-2 py-1 rounded bg-white border border-gray-200 text-gray-700 opacity-0 group-hover:opacity-100 transition-opacity"
                        :disabled="!!message._emojiDownloading"
                        @click.stop="onEmojiDownloadClick(message)"
                      >
                        {{ message._emojiDownloading ? '下载中...' : (message._emojiDownloaded ? '已下载' : '下载') }}
                      </button>
                    </template>
                    <div v-else class="px-3 py-2 text-sm max-w-sm relative msg-bubble whitespace-pre-wrap break-words leading-relaxed"
                      :class="message.isSent ? 'bg-[#95EC69] text-black bubble-tail-r' : 'bg-white text-gray-800 bubble-tail-l'">
                      {{ message.content }}
                    </div>
                  </div>
                  <template v-else-if="message.renderType === 'quote'">
                    <div
                      class="px-3 py-2 text-sm max-w-sm relative msg-bubble whitespace-pre-wrap break-words leading-relaxed"
                      :class="message.isSent ? 'bg-[#95EC69] text-black bubble-tail-r' : 'bg-white text-gray-800 bubble-tail-l'">
                      <span v-for="(seg, idx) in parseTextWithEmoji(message.content)" :key="idx">
                        <span v-if="seg.type === 'text'">{{ seg.content }}</span>
                        <img v-else :src="seg.emojiSrc" :alt="seg.content" class="inline-block w-[1.25em] h-[1.25em] align-text-bottom mx-px">
                      </span>
                    </div>
                    <div
                      v-if="message.quoteTitle || message.quoteContent"
                      class="mt-[5px] px-2 text-xs text-neutral-600 rounded max-w-[404px] max-h-[61px] flex items-center bg-[#e1e1e1]">
                      <div class="line-clamp-2 py-2">{{ message.quoteTitle }}: {{ message.quoteContent }}</div>
                    </div>
                  </template>
                  <div v-else-if="message.renderType === 'transfer'"
                    class="wechat-transfer-card msg-radius"
                    :class="[{ 'wechat-transfer-received': message.transferReceived, 'wechat-transfer-returned': isTransferReturned(message) }, message.isSent ? 'wechat-transfer-sent-side' : 'wechat-transfer-received-side']">
                    <div class="wechat-transfer-content">
                      <img src="/assets/images/wechat/wechat-returned.png" v-if="isTransferReturned(message)" class="wechat-transfer-icon" alt="">
                      <img src="/assets/images/wechat/wechat-trans-icon2.png" v-else-if="message.transferReceived" class="wechat-transfer-icon" alt="">
                      <img src="/assets/images/wechat/wechat-trans-icon1.png" v-else class="wechat-transfer-icon" alt="">
                      <div class="wechat-transfer-info">
                        <span class="wechat-transfer-amount" v-if="message.amount">¥{{ formatTransferAmount(message.amount) }}</span>
                        <span class="wechat-transfer-status">{{ getTransferTitle(message) }}</span>
                      </div>
                    </div>
                    <div class="wechat-transfer-bottom">
                      <span>微信转账</span>
                    </div>
                  </div>
                  <!-- 红包消息 - 微信风格橙色卡片 -->
                  <div v-else-if="message.renderType === 'redPacket'" class="wechat-redpacket-card wechat-special-card msg-radius"
                    :class="[{ 'wechat-redpacket-received': message.redPacketReceived }, message.isSent ? 'wechat-special-sent-side' : '']">
                    <div class="wechat-redpacket-content">
                      <img src="/assets/images/wechat/wechat-trans-icon3.png" v-if="!message.redPacketReceived" class="wechat-redpacket-icon" alt="">
                      <img src="/assets/images/wechat/wechat-trans-icon4.png" v-else class="wechat-redpacket-icon" alt="">
                      <div class="wechat-redpacket-info">
                        <span class="wechat-redpacket-text">{{ getRedPacketText(message) }}</span>
                        <span class="wechat-redpacket-status" v-if="message.redPacketReceived">已领取</span>
                      </div>
                    </div>
                    <div class="wechat-redpacket-bottom">
                      <span>微信红包</span>
                    </div>
                  </div>
                  <!-- 文本消息 -->
                  <div v-else-if="message.renderType === 'text'"
                    class="px-3 py-2 text-sm max-w-sm relative msg-bubble whitespace-pre-wrap break-words leading-relaxed"
                    :class="message.isSent ? 'bg-[#95EC69] text-black bubble-tail-r' : 'bg-white text-gray-800 bubble-tail-l'">
                    <span v-for="(seg, idx) in parseTextWithEmoji(message.content)" :key="idx">
                      <span v-if="seg.type === 'text'">{{ seg.content }}</span>
                      <img v-else :src="seg.emojiSrc" :alt="seg.content" class="inline-block w-[1.25em] h-[1.25em] align-text-bottom mx-px">
                    </span>
                  </div>
                  <!-- 表情消息 -->
                  <!-- 其他类型统一降级为普通文本展示 -->
                  <div v-else
                    class="px-3 py-2 text-xs max-w-sm relative msg-bubble whitespace-pre-wrap break-words leading-relaxed text-gray-700"
                    :class="message.isSent ? 'bg-[#95EC69] text-black bubble-tail-r' : 'bg-white text-gray-800 bubble-tail-l'">
                    {{ message.content || ('[' + (message.type || 'unknown') + '] 消息组件已移除') }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 未选择联系人时的提示 -->
      <div v-else class="flex-1 flex items-center justify-center">
        <div class="text-center text-gray-500">
          <div class="w-24 h-24 mx-auto mb-4 text-gray-300">
            <svg fill="currentColor" viewBox="0 0 20 20">
              <path d="M18 13V5a2 2 0 00-2-2H4a2 2 0 00-2 2v8a2 2 0 002 2h3l3 3 3-3h3a2 2 0 002-2zM5 7v14l11-7z"/>
            </svg>
          </div>
          <h3 class="text-lg font-medium text-gray-700 mb-2">微信聊天记录查看器</h3>
          <p class="text-gray-500">
            请选择一个联系人查看聊天记录
          </p>
        </div>
      </div>
    </div>

    <!-- 图片预览弹窗 (全局固定定位) -->
    <div v-if="previewImageUrl" 
      class="fixed inset-0 z-50 bg-black/90 flex items-center justify-center cursor-zoom-out"
      @click="closeImagePreview">
      <img :src="previewImageUrl" alt="预览" class="max-w-[90vw] max-h-[90vh] object-contain" @click.stop>
      <button 
        class="absolute top-4 right-4 text-white/80 hover:text-white p-2 rounded-full bg-black/30 hover:bg-black/50 transition-colors"
        @click="closeImagePreview">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
    </div>

    <div
      v-if="contextMenu.visible"
      class="fixed z-50 bg-white border border-gray-200 rounded-md shadow-lg text-sm"
      :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
      @click.stop
    >
      <button
        class="block w-full text-left px-3 py-2 hover:bg-gray-100"
        type="button"
        :disabled="contextMenu.disabled"
        @click="onOpenFolderClick"
      >
        打开文件夹
      </button>
    </div>

    <!-- 导出弹窗 -->
    <div v-if="exportModalOpen" class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="absolute inset-0 bg-black/40" @click="closeExportModal"></div>
      <div class="relative w-[780px] max-w-[92vw] bg-white rounded-lg shadow-xl border border-gray-200 overflow-hidden">
        <div class="px-5 py-4 border-b border-gray-200 flex items-center">
          <div class="text-base font-medium text-gray-900">导出聊天记录（离线 ZIP）</div>
          <button class="ml-auto text-gray-400 hover:text-gray-700" type="button" @click="closeExportModal">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <div class="p-5 max-h-[75vh] overflow-y-auto space-y-4">
          <div v-if="exportError" class="text-sm text-red-600 whitespace-pre-wrap">{{ exportError }}</div>
          <div v-if="privacyMode" class="text-sm bg-amber-50 border border-amber-200 text-amber-800 rounded-md px-3 py-2">
            已开启隐私模式：导出将隐藏会话/用户名/内容，并且不会打包头像与媒体。
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div class="text-sm font-medium text-gray-800 mb-2">范围</div>
              <div class="space-y-2 text-sm text-gray-700">
                <label class="flex items-center gap-2">
                  <input type="radio" value="current" v-model="exportScope" />
                  <span>当前会话</span>
                </label>
                <label class="flex items-center gap-2">
                  <input type="radio" value="selected" v-model="exportScope" />
                  <span>选择会话（批量）</span>
                </label>
                <label class="flex items-center gap-2">
                  <input type="radio" value="all" v-model="exportScope" />
                  <span>全部会话</span>
                </label>
                <label class="flex items-center gap-2">
                  <input type="radio" value="groups" v-model="exportScope" />
                  <span>仅群聊</span>
                </label>
                <label class="flex items-center gap-2">
                  <input type="radio" value="singles" v-model="exportScope" />
                  <span>仅单聊</span>
                </label>
              </div>

              <div v-if="exportScope === 'selected'" class="mt-3">
                <div class="flex items-center gap-2 mb-2">
                  <button
                    type="button"
                    class="text-xs px-2 py-1 rounded border border-gray-200"
                    :class="exportListTab === 'all' ? 'bg-[#03C160] text-white border-[#03C160]' : 'bg-white hover:bg-gray-50 text-gray-700'"
                    @click="exportListTab = 'all'"
                  >
                    全部 {{ exportContactCounts.total }}
                  </button>
                  <button
                    type="button"
                    class="text-xs px-2 py-1 rounded border border-gray-200"
                    :class="exportListTab === 'groups' ? 'bg-[#03C160] text-white border-[#03C160]' : 'bg-white hover:bg-gray-50 text-gray-700'"
                    @click="exportListTab = 'groups'"
                  >
                    群聊 {{ exportContactCounts.groups }}
                  </button>
                  <button
                    type="button"
                    class="text-xs px-2 py-1 rounded border border-gray-200"
                    :class="exportListTab === 'singles' ? 'bg-[#03C160] text-white border-[#03C160]' : 'bg-white hover:bg-gray-50 text-gray-700'"
                    @click="exportListTab = 'singles'"
                  >
                    单聊 {{ exportContactCounts.singles }}
                  </button>
                  <div class="ml-auto text-xs text-gray-500">点击 tab 筛选</div>
                </div>
                <div class="flex items-center gap-2 mb-2">
                  <input
                    v-model="exportSearchQuery"
                    type="text"
                    placeholder="搜索会话（名称/username）"
                    class="w-full px-3 py-2 text-sm rounded-md border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#03C160]/30"
                  />
                </div>
                <div class="border border-gray-200 rounded-md max-h-56 overflow-y-auto">
                  <div
                    v-for="c in exportFilteredContacts"
                    :key="c.username"
                    class="px-3 py-2 border-b border-gray-100 flex items-center gap-2 hover:bg-gray-50"
                  >
                    <input type="checkbox" :value="c.username" v-model="exportSelectedUsernames" />
                    <div class="w-9 h-9 rounded-md overflow-hidden bg-gray-200 flex-shrink-0" :class="{ 'privacy-blur': privacyMode }">
                      <img v-if="c.avatar" :src="c.avatar" :alt="c.name + '头像'" class="w-full h-full object-cover" />
                      <div v-else class="w-full h-full flex items-center justify-center text-xs font-bold text-gray-600">
                        {{ (c.name || c.username || '?').charAt(0) }}
                      </div>
                    </div>
                    <div class="min-w-0" :class="{ 'privacy-blur': privacyMode }">
                      <div class="text-sm text-gray-800 truncate">
                        {{ c.name }}
                        <span class="text-xs text-gray-500">{{ c.isGroup ? '（群）' : '' }}</span>
                      </div>
                      <div class="text-xs text-gray-500 truncate">{{ c.username }}</div>
                    </div>
                  </div>
                  <div v-if="exportFilteredContacts.length === 0" class="px-3 py-3 text-sm text-gray-500">
                    无匹配会话
                  </div>
                </div>
                <div class="mt-2 text-xs text-gray-500">
                  已选 {{ exportSelectedUsernames.length }} 个会话
                </div>
              </div>
            </div>

            <div class="space-y-4">
              <div>
                <div class="text-sm font-medium text-gray-800 mb-2">格式</div>
                <div class="flex items-center gap-4 text-sm text-gray-700">
                  <label class="flex items-center gap-2">
                    <input type="radio" value="json" v-model="exportFormat" />
                    <span>JSON</span>
                  </label>
                  <label class="flex items-center gap-2">
                    <input type="radio" value="txt" v-model="exportFormat" />
                    <span>TXT</span>
                  </label>
                </div>
              </div>

              <div>
                <div class="text-sm font-medium text-gray-800 mb-2">时间范围（可选）</div>
                <div class="grid grid-cols-2 gap-2">
                  <input
                    v-model="exportStartLocal"
                    type="datetime-local"
                    class="px-3 py-2 text-sm rounded-md border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#03C160]/30"
                  />
                  <input
                    v-model="exportEndLocal"
                    type="datetime-local"
                    class="px-3 py-2 text-sm rounded-md border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#03C160]/30"
                  />
                </div>
                <div class="flex items-center gap-2 mt-2">
                  <button type="button" class="text-xs px-2 py-1 rounded border border-gray-200 hover:bg-gray-50" @click="exportStartLocal=''; exportEndLocal=''">全部</button>
                  <button type="button" class="text-xs px-2 py-1 rounded border border-gray-200 hover:bg-gray-50" @click="applyExportQuickRangeDays(7)">最近7天</button>
                  <button type="button" class="text-xs px-2 py-1 rounded border border-gray-200 hover:bg-gray-50" @click="applyExportQuickRangeDays(30)">最近30天</button>
                </div>
              </div>

              <div>
                <div class="text-sm font-medium text-gray-800 mb-2">媒体（离线）</div>
                <label class="flex items-center gap-2 text-sm text-gray-700">
                  <input type="checkbox" v-model="exportIncludeMedia" :disabled="privacyMode" />
                  <span>打包媒体文件到 ZIP（图片/表情/视频/语音/文件）</span>
                </label>
                <div class="grid grid-cols-2 gap-2 mt-2 text-sm text-gray-700">
                  <label class="flex items-center gap-2" :class="(exportIncludeMedia && !privacyMode) ? '' : 'opacity-50'">
                    <input type="checkbox" value="image" v-model="exportMediaKinds" :disabled="!exportIncludeMedia || privacyMode" />
                    <span>图片</span>
                  </label>
                  <label class="flex items-center gap-2" :class="(exportIncludeMedia && !privacyMode) ? '' : 'opacity-50'">
                    <input type="checkbox" value="emoji" v-model="exportMediaKinds" :disabled="!exportIncludeMedia || privacyMode" />
                    <span>表情</span>
                  </label>
                  <label class="flex items-center gap-2" :class="(exportIncludeMedia && !privacyMode) ? '' : 'opacity-50'">
                    <input type="checkbox" value="video" v-model="exportMediaKinds" :disabled="!exportIncludeMedia || privacyMode" />
                    <span>视频</span>
                  </label>
                  <label class="flex items-center gap-2" :class="(exportIncludeMedia && !privacyMode) ? '' : 'opacity-50'">
                    <input type="checkbox" value="voice" v-model="exportMediaKinds" :disabled="!exportIncludeMedia || privacyMode" />
                    <span>语音</span>
                  </label>
                  <label class="flex items-center gap-2" :class="(exportIncludeMedia && !privacyMode) ? '' : 'opacity-50'">
                    <input type="checkbox" value="file" v-model="exportMediaKinds" :disabled="!exportIncludeMedia || privacyMode" />
                    <span>文件</span>
                  </label>
                  <label class="flex items-center gap-2" :class="(exportIncludeMedia && !privacyMode) ? '' : 'opacity-50'">
                    <input type="checkbox" value="video_thumb" v-model="exportMediaKinds" :disabled="!exportIncludeMedia || privacyMode" />
                    <span>视频缩略图</span>
                  </label>
                </div>
              </div>

              <div>
                <div class="text-sm font-medium text-gray-800 mb-2">文件名（可选）</div>
                <input
                  v-model="exportFileName"
                  type="text"
                  placeholder="例如：我的微信导出_2025-12-23.zip"
                  class="w-full px-3 py-2 text-sm rounded-md border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#03C160]/30"
                />
                <div class="mt-1 text-xs text-gray-500">不填则自动生成（输出位置：output/exports/{账号}/）。</div>
              </div>

              <div class="space-y-2">
                <label class="flex items-center gap-2 text-sm text-gray-700">
                  <input type="checkbox" v-model="exportIncludeHidden" />
                  <span>包含隐藏会话（仅对“全部/群/单”有效）</span>
                </label>
                <label class="flex items-center gap-2 text-sm text-gray-700">
                  <input type="checkbox" v-model="exportIncludeOfficial" />
                  <span>包含公众号/官方会话（仅对“全部/群/单”有效）</span>
                </label>
              </div>
            </div>
          </div>

          <div v-if="exportJob" class="border border-gray-200 rounded-md bg-gray-50 p-4">
            <div class="flex items-center justify-between">
              <div class="text-sm font-medium text-gray-900">任务：{{ exportJob.exportId }}</div>
              <div class="text-xs text-gray-600">状态：{{ exportJob.status }}</div>
            </div>
            <div class="mt-2 text-xs text-gray-700 space-y-2">
              <div class="flex items-center justify-between">
                <div>会话：{{ exportJob.progress?.conversationsDone || 0 }}/{{ exportJob.progress?.conversationsTotal || 0 }}</div>
                <div class="text-gray-600">{{ exportOverallPercent }}%</div>
              </div>
              <div class="h-2 rounded-full bg-white border border-gray-200 overflow-hidden">
                <div
                  class="h-full bg-[#03C160] transition-all duration-300"
                  :style="{ width: exportOverallPercent + '%' }"
                ></div>
              </div>

              <div v-if="exportJob.progress?.currentConversationUsername" class="space-y-1">
                <div class="flex items-center justify-between gap-2">
                  <div class="truncate">
                    当前：{{ exportJob.progress?.currentConversationName || exportJob.progress?.currentConversationUsername }}
                    （{{ exportJob.progress?.currentConversationMessagesExported || 0 }}/{{ exportJob.progress?.currentConversationMessagesTotal || 0 }}）
                  </div>
                  <div class="text-gray-600">
                    <span v-if="exportCurrentPercent != null">{{ exportCurrentPercent }}%</span>
                    <span v-else>…</span>
                  </div>
                </div>
                <div class="h-2 rounded-full bg-white border border-gray-200 overflow-hidden">
                  <div
                    v-if="exportCurrentPercent != null"
                    class="h-full bg-sky-500 transition-all duration-300"
                    :style="{ width: exportCurrentPercent + '%' }"
                  ></div>
                  <div v-else class="h-full bg-sky-500/60 animate-pulse" style="width: 30%"></div>
                </div>
              </div>

              <div>消息：{{ exportJob.progress?.messagesExported || 0 }}；媒体：{{ exportJob.progress?.mediaCopied || 0 }}；缺失：{{ exportJob.progress?.mediaMissing || 0 }}</div>
            </div>

            <div class="mt-3 flex items-center gap-2">
              <a
                v-if="exportJob.status === 'done'"
                class="text-sm px-3 py-2 rounded-md bg-[#03C160] text-white hover:bg-[#02a650]"
                :href="getExportDownloadUrl(exportJob.exportId)"
                target="_blank"
              >
                下载 ZIP
              </a>
              <button
                v-if="exportJob.status === 'running'"
                class="text-sm px-3 py-2 rounded-md bg-white border border-gray-200 hover:bg-gray-50"
                type="button"
                @click="cancelCurrentExport"
              >
                取消任务
              </button>
            </div>

            <div v-if="exportJob.status === 'error'" class="mt-2 text-sm text-red-600 whitespace-pre-wrap">
              {{ exportJob.error || '导出失败' }}
            </div>
          </div>
        </div>

        <div class="px-5 py-4 border-t border-gray-200 flex items-center justify-end gap-2">
          <button class="text-sm px-3 py-2 rounded-md bg-white border border-gray-200 hover:bg-gray-50" type="button" @click="closeExportModal">
            关闭
          </button>
          <button
            class="text-sm px-3 py-2 rounded-md bg-[#03C160] text-white hover:bg-[#02a650] disabled:opacity-60"
            type="button"
            @click="startChatExport"
            :disabled="isExportCreating"
          >
            {{ isExportCreating ? '创建中...' : '开始导出' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick, defineComponent, h } from 'vue'

definePageMeta({
  key: 'chat'
})

import { useApi } from '~/composables/useApi'
import { parseTextWithEmoji } from '~/utils/wechat-emojis'
import wechatPcLogoUrl from '~/assets/images/wechat/WeChat-Icon-Logo.wine.svg'
import zipIconUrl from '~/assets/images/wechat/zip.png'
import pdfIconUrl from '~/assets/images/wechat/pdf.png'
import wordIconUrl from '~/assets/images/wechat/word.png'
import excelIconUrl from '~/assets/images/wechat/excel.png'

// 根据文件名获取对应的图标URL
const getFileIconUrl = (fileName) => {
  if (!fileName) return zipIconUrl
  const ext = String(fileName).split('.').pop()?.toLowerCase() || ''
  switch (ext) {
    case 'pdf':
      return pdfIconUrl
    case 'doc':
    case 'docx':
      return wordIconUrl
    case 'xls':
    case 'xlsx':
    case 'csv':
      return excelIconUrl
    case 'zip':
    case 'rar':
    case '7z':
    case 'tar':
    case 'gz':
    default:
      return zipIconUrl
  }
}

// 设置页面标题
useHead({
  title: '聊天记录查看器 - 微信数据分析助手'
})

const route = useRoute()

const routeUsername = computed(() => {
  const raw = route.params.username
  return (Array.isArray(raw) ? raw[0] : raw) || ''
})

const buildChatPath = (username) => {
  return username ? `/chat/${encodeURIComponent(username)}` : '/chat'
}

// 响应式数据
const selectedContact = ref(null)

// 隐私模式
const privacyMode = ref(false)

// 联系人数据
const contacts = ref([])

const searchQuery = ref('')

const isLoadingContacts = ref(false)
const contactsError = ref('')
const selectedAccount = ref(null)

const availableAccounts = ref([])

const allMessages = ref({})

const messagesMeta = ref({})
const isLoadingMessages = ref(false)
const messagesError = ref('')

// 导出（离线 zip）
const exportModalOpen = ref(false)
const isExportCreating = ref(false)
const exportError = ref('')

// current: 当前会话（映射为 selected + 单个 username）
const exportScope = ref('current') // current | selected | all | groups | singles
const exportFormat = ref('json') // json | txt
const exportIncludeMedia = ref(true)
const exportMediaKinds = ref(['image', 'emoji', 'video', 'video_thumb', 'voice', 'file'])
const exportIncludeHidden = ref(false)
const exportIncludeOfficial = ref(false)

const exportStartLocal = ref('') // datetime-local
const exportEndLocal = ref('') // datetime-local
const exportFileName = ref('')

const exportSearchQuery = ref('')
const exportListTab = ref('all') // all | groups | singles
const exportSelectedUsernames = ref([])

const exportJob = ref(null)
let exportPollTimer = null
let exportEventSource = null

const _clamp01 = (n) => Math.min(1, Math.max(0, n))
const _asNumber = (v) => {
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}

const exportOverallPercent = computed(() => {
  const job = exportJob.value
  const p = job?.progress || {}
  const total = _asNumber(p.conversationsTotal)
  const done = _asNumber(p.conversationsDone)
  if (total <= 0) return 0

  const currentTotal = _asNumber(p.currentConversationMessagesTotal)
  const currentDone = _asNumber(p.currentConversationMessagesExported)
  const fracCurrent = currentTotal > 0 ? _clamp01(currentDone / currentTotal) : 0
  const overall = _clamp01((done + (job?.status === 'running' ? fracCurrent : 0)) / total)
  return Math.round(overall * 100)
})

const exportCurrentPercent = computed(() => {
  const p = exportJob.value?.progress || {}
  const total = _asNumber(p.currentConversationMessagesTotal)
  const done = _asNumber(p.currentConversationMessagesExported)
  if (total <= 0) return null
  return Math.round(_clamp01(done / total) * 100)
})

const exportFilteredContacts = computed(() => {
  const q = String(exportSearchQuery.value || '').trim().toLowerCase()
  let list = Array.isArray(contacts.value) ? contacts.value : []

  const tab = String(exportListTab.value || 'all')
  if (tab === 'groups') list = list.filter((c) => !!c?.isGroup)
  if (tab === 'singles') list = list.filter((c) => !c?.isGroup)

  if (!q) return list
  return list.filter((c) => {
    const name = String(c?.name || '').toLowerCase()
    const username = String(c?.username || '').toLowerCase()
    return name.includes(q) || username.includes(q)
  })
})

const exportContactCounts = computed(() => {
  const list = Array.isArray(contacts.value) ? contacts.value : []
  const total = list.length
  const groups = list.filter((c) => !!c?.isGroup).length
  return { total, groups, singles: total - groups }
})

const toUnixSeconds = (datetimeLocal) => {
  const v = String(datetimeLocal || '').trim()
  if (!v) return null
  const d = new Date(v)
  const ms = d.getTime()
  if (!ms || Number.isNaN(ms)) return null
  return Math.floor(ms / 1000)
}

const stopExportPolling = () => {
  if (exportEventSource) {
    try {
      exportEventSource.close()
    } catch (e) {
      // ignore
    }
    exportEventSource = null
  }
  if (exportPollTimer) {
    clearInterval(exportPollTimer)
    exportPollTimer = null
  }
}

const startExportHttpPolling = (exportId) => {
  if (!exportId) return
  const api = useApi()
  exportPollTimer = setInterval(async () => {
    try {
      const resp = await api.getChatExport(exportId)
      exportJob.value = resp?.job || exportJob.value

      const st = String(exportJob.value?.status || '')
      if (st === 'done' || st === 'error' || st === 'cancelled') {
        stopExportPolling()
      }
    } catch (e) {
      // keep polling; transient errors are possible while exporting
    }
  }, 1200)
}

const startExportPolling = (exportId) => {
  stopExportPolling()
  if (!exportId) return

  if (process.client && typeof window !== 'undefined' && typeof EventSource !== 'undefined') {
    const base = 'http://localhost:8000'
    const url = `${base}/api/chat/exports/${encodeURIComponent(String(exportId))}/events`
    try {
      exportEventSource = new EventSource(url)
      exportEventSource.onmessage = (ev) => {
        try {
          const next = JSON.parse(String(ev.data || '{}'))
          exportJob.value = next || exportJob.value
          const st = String(exportJob.value?.status || '')
          if (st === 'done' || st === 'error' || st === 'cancelled') {
            stopExportPolling()
          }
        } catch (e) {
          // ignore
        }
      }
      exportEventSource.onerror = () => {
        // fallback to HTTP polling
        try {
          exportEventSource?.close()
        } catch (e) {
          // ignore
        }
        exportEventSource = null
        if (!exportPollTimer) startExportHttpPolling(exportId)
      }
      return
    } catch (e) {
      exportEventSource = null
    }
  }

  startExportHttpPolling(exportId)
}

const openExportModal = () => {
  exportModalOpen.value = true
  exportError.value = ''
  exportListTab.value = 'all'

  if (privacyMode.value) {
    exportIncludeMedia.value = false
  }

  if (selectedContact.value?.username) {
    exportScope.value = 'current'
  } else {
    exportScope.value = 'all'
  }
}

const closeExportModal = () => {
  exportModalOpen.value = false
  exportError.value = ''
}

watch(exportModalOpen, (open) => {
  if (!process.client) return
  if (!open) {
    stopExportPolling()
    return
  }

  const exportId = exportJob.value?.exportId
  const st = String(exportJob.value?.status || '')
  if (exportId && (st === 'queued' || st === 'running')) {
    startExportPolling(exportId)
  }
})

const getExportDownloadUrl = (exportId) => {
  const base = process.client ? 'http://localhost:8000' : ''
  return `${base}/api/chat/exports/${encodeURIComponent(String(exportId || ''))}/download`
}

const startChatExport = async () => {
  exportError.value = ''
  if (!selectedAccount.value) {
    exportError.value = '未选择账号'
    return
  }

  let scope = exportScope.value
  let usernames = []
  if (scope === 'current') {
    scope = 'selected'
    if (selectedContact.value?.username) {
      usernames = [selectedContact.value.username]
    }
  } else if (scope === 'selected') {
    usernames = Array.isArray(exportSelectedUsernames.value) ? exportSelectedUsernames.value.filter(Boolean) : []
  }

  if (scope === 'selected' && (!usernames || usernames.length === 0)) {
    exportError.value = '请选择至少一个会话'
    return
  }

  const startTime = toUnixSeconds(exportStartLocal.value)
  const endTime = toUnixSeconds(exportEndLocal.value)
  if (startTime && endTime && startTime > endTime) {
    exportError.value = '时间范围不合法：开始时间不能晚于结束时间'
    return
  }

  isExportCreating.value = true
  try {
    const api = useApi()
    const resp = await api.createChatExport({
      account: selectedAccount.value,
      scope,
      usernames,
      format: exportFormat.value,
      start_time: startTime,
      end_time: endTime,
      include_hidden: exportIncludeHidden.value,
      include_official: exportIncludeOfficial.value,
      include_media: exportIncludeMedia.value && !privacyMode.value,
      media_kinds: (exportIncludeMedia.value && !privacyMode.value) ? exportMediaKinds.value : [],
      privacy_mode: !!privacyMode.value,
      file_name: exportFileName.value || null
    })

    exportJob.value = resp?.job || null
    const exportId = exportJob.value?.exportId
    if (exportId) startExportPolling(exportId)
  } catch (e) {
    exportError.value = e?.message || '创建导出任务失败'
  } finally {
    isExportCreating.value = false
  }
}

const cancelCurrentExport = async () => {
  const exportId = exportJob.value?.exportId
  if (!exportId) return

  try {
    const api = useApi()
    await api.cancelChatExport(exportId)
    const resp = await api.getChatExport(exportId)
    exportJob.value = resp?.job || exportJob.value
  } catch (e) {
    exportError.value = e?.message || '取消导出失败'
  }
}

const applyExportQuickRangeDays = (days) => {
  const now = new Date()
  const end = new Date(now.getTime())
  const start = new Date(now.getTime() - Number(days) * 24 * 3600 * 1000)
  const pad = (n) => String(n).padStart(2, '0')
  const fmt = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
  exportStartLocal.value = fmt(start)
  exportEndLocal.value = fmt(end)
}

const messagePageSize = 50

const messageContainerRef = ref(null)
const activeMessagesFor = ref('')

// 图片预览状态
const previewImageUrl = ref(null)

const openImagePreview = (url) => {
  previewImageUrl.value = url
  document.body.style.overflow = 'hidden'
}

const closeImagePreview = () => {
  previewImageUrl.value = null
  document.body.style.overflow = ''
}

const voiceRefs = ref({})
const currentPlayingVoice = ref(null)
const playingVoiceId = ref(null)

const setVoiceRef = (id, el) => {
  if (el) {
    voiceRefs.value[id] = el
    el.onended = () => {
      if (playingVoiceId.value === id) {
        playingVoiceId.value = null
        currentPlayingVoice.value = null
      }
    }
  }
}

const playVoice = (message) => {
  const audio = voiceRefs.value[message.id]
  if (!audio) return

  // 停止当前播放的语音
  if (currentPlayingVoice.value && currentPlayingVoice.value !== audio) {
    currentPlayingVoice.value.pause()
    currentPlayingVoice.value.currentTime = 0
    playingVoiceId.value = null
  }

  if (audio.paused) {
    audio.play()
    currentPlayingVoice.value = audio
    playingVoiceId.value = message.id
  } else {
    audio.pause()
    audio.currentTime = 0
    currentPlayingVoice.value = null
    playingVoiceId.value = null
  }
}

// 将毫秒转换为秒（voiceLength 存储的是毫秒）
const getVoiceDurationInSeconds = (durationMs) => {
  const ms = parseInt(durationMs) || 0
  return Math.round(ms / 1000)
}

// 根据语音时长计算宽度（基于秒数）
const getVoiceWidth = (durationMs) => {
  const seconds = getVoiceDurationInSeconds(durationMs)
  const minWidth = 80
  const maxWidth = 200
  const width = Math.min(maxWidth, minWidth + seconds * 4)
  return `${width}px`
}

const contextMenu = ref({ visible: false, x: 0, y: 0, message: null, kind: '', disabled: false })

const closeContextMenu = () => {
  contextMenu.value = { visible: false, x: 0, y: 0, message: null, kind: '', disabled: false }
}

const openMediaContextMenu = (e, message, kind) => {
  if (!process.client) return
  e.preventDefault()
  e.stopPropagation()

  let actualKind = kind

  let disabled = false
  if (kind === 'voice') {
    disabled = !message?.serverId
  } else if (kind === 'file') {
    disabled = !message?.fileMd5
  } else if (kind === 'image') {
    disabled = !(message?.imageMd5 || message?.imageFileId)
  } else if (kind === 'emoji') {
    disabled = !message?.emojiMd5
  } else if (kind === 'video') {
    if (message?.videoMd5 || message?.videoFileId) {
      disabled = false
      actualKind = 'video'
    } else if (message?.videoThumbMd5 || message?.videoThumbFileId) {
      disabled = false
      actualKind = 'video_thumb'
    } else {
      disabled = true
    }
  }

  contextMenu.value = {
    visible: true,
    x: e.clientX,
    y: e.clientY,
    message,
    kind: actualKind,
    disabled
  }
}

const onOpenFolderClick = async () => {
  if (contextMenu.value.disabled) return
  const api = useApi()
  const m = contextMenu.value.message
  const kind = contextMenu.value.kind

  try {
    if (!selectedAccount.value) return
    if (!selectedContact.value?.username) return

    const params = {
      account: selectedAccount.value,
      username: selectedContact.value.username,
      kind
    }

    if (kind === 'voice') {
      params.server_id = m.serverId
    } else if (kind === 'file') {
      params.md5 = m.fileMd5
    } else if (kind === 'image') {
      if (m.imageMd5) params.md5 = m.imageMd5
      else if (m.imageFileId) params.file_id = m.imageFileId
    } else if (kind === 'emoji') {
      params.md5 = m.emojiMd5
    } else if (kind === 'video') {
      params.md5 = m.videoMd5
      if (m.videoFileId) params.file_id = m.videoFileId
    } else if (kind === 'video_thumb') {
      params.md5 = m.videoThumbMd5
      if (m.videoThumbFileId) params.file_id = m.videoThumbFileId
    }

    await api.openChatMediaFolder(params)
  } finally {
    closeContextMenu()
  }
}

// 消息样式展示数据
// 计算属性：当前选中联系人的消息
const messages = computed(() => {
  if (!selectedContact.value) return []
  return allMessages.value[selectedContact.value.username] || []
})

// 智能时间格式化：今天显示时间，昨天显示"昨天 HH:MM"，本周显示"星期X HH:MM"，本年显示"MM月DD日 HH:MM"，跨年显示"YYYY年MM月DD日 HH:MM"
const formatSmartTime = (ts) => {
  if (!ts) return ''
  try {
    const d = new Date(Number(ts) * 1000)
    const now = new Date()
    const hh = String(d.getHours()).padStart(2, '0')
    const mm = String(d.getMinutes()).padStart(2, '0')
    const timeStr = `${hh}:${mm}`

    // 计算日期差异（基于日历日期，而非24小时）
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const targetStart = new Date(d.getFullYear(), d.getMonth(), d.getDate())
    const dayDiff = Math.floor((todayStart - targetStart) / (1000 * 60 * 60 * 24))

    // 今天
    if (dayDiff === 0) {
      return timeStr
    }

    // 昨天
    if (dayDiff === 1) {
      return `昨天 ${timeStr}`
    }

    // 本周内（2-6天前，显示星期）
    if (dayDiff >= 2 && dayDiff <= 6) {
      const weekDays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
      return `${weekDays[d.getDay()]} ${timeStr}`
    }

    // 本年内
    const month = d.getMonth() + 1
    const day = d.getDate()
    if (d.getFullYear() === now.getFullYear()) {
      return `${month}月${day}日 ${timeStr}`
    }

    // 跨年
    return `${d.getFullYear()}年${month}月${day}日 ${timeStr}`
  } catch {
    return ''
  }
}

const formatTimeDivider = (ts) => {
  return formatSmartTime(ts)
}

const formatMessageTime = (ts) => {
  if (!ts) return ''
  try {
    const d = new Date(Number(ts) * 1000)
    const hh = String(d.getHours()).padStart(2, '0')
    const mm = String(d.getMinutes()).padStart(2, '0')
    return `${hh}:${mm}`
  } catch {
    return ''
  }
}

const formatMessageFullTime = (ts) => {
  if (!ts) return ''
  try {
    const d = new Date(Number(ts) * 1000)
    const yyyy = String(d.getFullYear())
    const MM = String(d.getMonth() + 1).padStart(2, '0')
    const dd = String(d.getDate()).padStart(2, '0')
    const hh = String(d.getHours()).padStart(2, '0')
    const mm = String(d.getMinutes()).padStart(2, '0')
    const ss = String(d.getSeconds()).padStart(2, '0')
    return `${yyyy}-${MM}-${dd} ${hh}:${mm}:${ss}`
  } catch {
    return ''
  }
}

const formatFileSize = (size) => {
  if (!size) return ''
  const s = String(size).trim()
  const num = parseFloat(s)
  if (isNaN(num)) return s
  if (num < 1024) return `${num} B`
  if (num < 1024 * 1024) return `${(num / 1024).toFixed(2)} KB`
  return `${(num / 1024 / 1024).toFixed(2)} MB`
}

const formatTransferAmount = (amount) => {
  const s = String(amount ?? '').trim()
  if (!s) return ''
  return s.replace(/[￥¥]/g, '').trim()
}

const getRedPacketText = (message) => {
  const text = String(message?.content ?? '').trim()
  if (!text || text === '[Red Packet]') return '恭喜发财，大吉大利'
  return text
}

// 文件类型图标组件
const FileIconPdf = defineComponent({
  render() {
    return h('svg', { viewBox: '0 0 24 24', fill: 'none', class: 'text-red-500' }, [
      h('path', { d: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z', stroke: 'currentColor', 'stroke-width': '1.5', fill: 'none' }),
      h('path', { d: 'M14 2v6h6', stroke: 'currentColor', 'stroke-width': '1.5' }),
      h('text', { x: '7', y: '17', 'font-size': '6', fill: 'currentColor', 'font-weight': 'bold' }, 'PDF')
    ])
  }
})

const FileIconZip = defineComponent({
  render() {
    return h('svg', { viewBox: '0 0 24 24', fill: 'none', class: 'text-yellow-600' }, [
      h('path', { d: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z', stroke: 'currentColor', 'stroke-width': '1.5', fill: 'none' }),
      h('path', { d: 'M14 2v6h6', stroke: 'currentColor', 'stroke-width': '1.5' }),
      h('text', { x: '7', y: '17', 'font-size': '6', fill: 'currentColor', 'font-weight': 'bold' }, 'ZIP')
    ])
  }
})

const FileIconDoc = defineComponent({
  render() {
    return h('svg', { viewBox: '0 0 24 24', fill: 'none', class: 'text-blue-600' }, [
      h('path', { d: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z', stroke: 'currentColor', 'stroke-width': '1.5', fill: 'none' }),
      h('path', { d: 'M14 2v6h6', stroke: 'currentColor', 'stroke-width': '1.5' }),
      h('text', { x: '5', y: '17', 'font-size': '5', fill: 'currentColor', 'font-weight': 'bold' }, 'DOC')
    ])
  }
})

const FileIconXls = defineComponent({
  render() {
    return h('svg', { viewBox: '0 0 24 24', fill: 'none', class: 'text-green-600' }, [
      h('path', { d: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 2l5 5h-5V4zM6 20V4h6v6h6v10H6z', stroke: 'currentColor', 'stroke-width': '1.5', fill: 'none' }),
      h('path', { d: 'M14 2v6h6', stroke: 'currentColor', 'stroke-width': '1.5' }),
      h('text', { x: '6', y: '17', 'font-size': '5', fill: 'currentColor', 'font-weight': 'bold' }, 'XLS')
    ])
  }
})

const FileIconPpt = defineComponent({
  render() {
    return h('svg', { viewBox: '0 0 24 24', fill: 'none', class: 'text-orange-500' }, [
      h('path', { d: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z', stroke: 'currentColor', 'stroke-width': '1.5', fill: 'none' }),
      h('path', { d: 'M14 2v6h6', stroke: 'currentColor', 'stroke-width': '1.5' }),
      h('text', { x: '6', y: '17', 'font-size': '5', fill: 'currentColor', 'font-weight': 'bold' }, 'PPT')
    ])
  }
})

const FileIconTxt = defineComponent({
  render() {
    return h('svg', { viewBox: '0 0 24 24', fill: 'none', class: 'text-gray-500' }, [
      h('path', { d: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z', stroke: 'currentColor', 'stroke-width': '1.5', fill: 'none' }),
      h('path', { d: 'M14 2v6h6', stroke: 'currentColor', 'stroke-width': '1.5' }),
      h('text', { x: '6', y: '17', 'font-size': '5', fill: 'currentColor', 'font-weight': 'bold' }, 'TXT')
    ])
  }
})

const FileIconDefault = defineComponent({
  render() {
    return h('svg', { viewBox: '0 0 24 24', fill: 'currentColor', class: 'text-gray-400' }, [
      h('path', { d: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 2l5 5h-5V4zM6 20V4h6v6h6v10H6z' })
    ])
  }
})

// 根据文件名获取对应图标
const getFileIcon = (fileName) => {
  if (!fileName) return FileIconDefault
  const ext = String(fileName).split('.').pop()?.toLowerCase() || ''
  switch (ext) {
    case 'pdf': return FileIconPdf
    case 'zip': case 'rar': case '7z': case 'tar': case 'gz': return FileIconZip
    case 'doc': case 'docx': return FileIconDoc
    case 'xls': case 'xlsx': case 'csv': return FileIconXls
    case 'ppt': case 'pptx': return FileIconPpt
    case 'txt': case 'md': case 'log': return FileIconTxt
    default: return FileIconDefault
  }
}

// 文件点击事件 - 打开文件所在文件夹
const onFileClick = async (message) => {
  if (!message?.fileMd5) return
  const api = useApi()
  
  try {
    if (!selectedAccount.value) return
    if (!selectedContact.value?.username) return
    
    await api.openChatMediaFolder({
      account: selectedAccount.value,
      username: selectedContact.value.username,
      kind: 'file',
      md5: message.fileMd5
    })
  } catch (err) {
    console.error('打开文件夹失败:', err)
  }
}

const isTransferReturned = (message) => {
  const paySubType = String(message?.paySubType || '').trim()
  if (paySubType === '4' || paySubType === '9') return true
  const s = String(message?.transferStatus || '').trim()
  const c = String(message?.content || '').trim()
  const text = `${s} ${c}`.trim()
  if (!text) return false
  return text.includes('退回') || text.includes('退还')
}

const getTransferTitle = (message) => {
  const paySubType = String(message.paySubType || '').trim()
  // paysubtype 含义：
  // 1=不明确 3=已收款/接收转账 4=对方退回给你 8=发起转账 9=被对方退回 10=已过期
  // 优先使用后端计算的 transferStatus（如果有）
  if (message.transferStatus) return message.transferStatus
  switch (paySubType) {
    case '1': return '转账'
    case '3': return message.isSent ? '已收款' : '已被接收'
    case '8': return '发起转账'
    case '4': return '已退还'
    case '9': return '已被退还'
    case '10': return '已过期'
  }
  if (message.content && message.content !== '转账' && message.content !== '[转账]') {
    return message.content
  }
  return '转账'
}

const renderMessages = computed(() => {
  const list = messages.value || []
  let prevTs = 0
  return list.map((m) => {
    const ts = Number(m.createTime || 0)
    const show = !prevTs || (ts && Math.abs(ts - prevTs) >= 300)
    if (ts) prevTs = ts
    return {
      ...m,
      showTimeDivider: !!show,
      timeDivider: formatTimeDivider(ts)
    }
  })
})

const filteredContacts = computed(() => {
  const q = (searchQuery.value || '').trim().toLowerCase()
  if (!q) return contacts.value
  return contacts.value.filter((c) => {
    const name = (c.name || '').toLowerCase()
    const username = (c.username || '').toLowerCase()
    return name.includes(q) || username.includes(q)
  })
})

const hasMoreMessages = computed(() => {
  if (!selectedContact.value) return false
  const key = selectedContact.value.username
  const meta = messagesMeta.value[key]
  if (!meta) return false
  if (meta.hasMore != null) return !!meta.hasMore
  const total = Number(meta.total || 0)
  const loaded = messages.value.length
  return total > loaded
})

// 已移除切换标签逻辑

// 选择联系人
const selectContact = async (contact, options = {}) => {
  if (!contact) return
  selectedContact.value = contact
  const username = contact?.username || ''
  if (!username) return
  if (options.syncRoute !== false && username) {
    const current = routeUsername.value || ''
    if (current !== username) {
      await navigateTo(buildChatPath(username), { replace: options.replaceRoute !== false })
    }
  }
  loadMessages({ username, reset: true })
}

const applyRouteSelection = async () => {
  if (!contacts.value || contacts.value.length === 0) {
    selectedContact.value = null
    return
  }

  const requested = routeUsername.value || ''
  if (requested) {
    const matched = contacts.value.find((c) => c.username === requested)
    if (matched) {
      if (selectedContact.value?.username !== matched.username) {
        await selectContact(matched, { syncRoute: false })
      }
      return
    }
  }

  await selectContact(contacts.value[0], { syncRoute: true, replaceRoute: true })
}

// 已移除样式选择逻辑

// 默认选择第一个联系人
onMounted(() => {
  loadContacts()
})

const loadContacts = async () => {
  const api = useApi()
  isLoadingContacts.value = true
  contactsError.value = ''

  try {
    const accountsResp = await api.listChatAccounts()
    const accounts = accountsResp?.accounts || []
    availableAccounts.value = accounts
    selectedAccount.value = selectedAccount.value || accountsResp?.default_account || accounts[0] || null

    if (!selectedAccount.value) {
      contacts.value = []
      selectedContact.value = null
      contactsError.value = accountsResp?.message || '未检测到已解密账号，请先解密数据库。'
      return
    }

    await loadSessionsForSelectedAccount()
  } catch (e) {
    contacts.value = []
    selectedContact.value = null
    contactsError.value = e?.message || '加载联系人失败'
  } finally {
    isLoadingContacts.value = false
  }
}

const loadSessionsForSelectedAccount = async () => {
  const api = useApi()

  if (!selectedAccount.value) {
    contacts.value = []
    selectedContact.value = null
    return
  }

  const sessionsResp = await api.listChatSessions({
    account: selectedAccount.value,
    limit: 400,
    include_hidden: false,
    include_official: false
  })

  const sessions = sessionsResp?.sessions || []
  contacts.value = sessions.map((s) => ({
    id: s.id,
    name: s.name || s.username || s.id,
    avatar: s.avatar || null,
    lastMessage: s.lastMessage || '',
    lastMessageTime: s.lastMessageTime || '',
    unreadCount: s.unreadCount || 0,
    isGroup: !!s.isGroup,
    username: s.username
  }))

  allMessages.value = {}
  messagesMeta.value = {}
  messagesError.value = ''
  selectedContact.value = null

  await applyRouteSelection()
}

const onAccountChange = async () => {
  try {
    isLoadingContacts.value = true
    contactsError.value = ''
    await loadSessionsForSelectedAccount()
  } catch (e) {
    contactsError.value = e?.message || '加载联系人失败'
  } finally {
    isLoadingContacts.value = false
  }
}

const normalizeMessage = (msg) => {
  const isSent = !!msg.isSent
  const sender = isSent ? '我' : (msg.senderDisplayName || msg.senderUsername || selectedContact.value?.name || '')
  const fallbackAvatar = (!isSent && !selectedContact.value?.isGroup) ? (selectedContact.value?.avatar || null) : null

  const mediaBase = process.client ? 'http://localhost:8000' : ''
  const normalizeMaybeUrl = (u) => (typeof u === 'string' ? u.trim() : '')
  const isUsableMediaUrl = (u) => {
    const v = normalizeMaybeUrl(u)
    if (!v) return false
    return (
      /^https?:\/\//i.test(v)
      || /^blob:/i.test(v)
      || /^data:/i.test(v)
      || /^\/api\/chat\/media\//i.test(v)
    )
  }

  const localEmojiUrl = msg.emojiMd5 ? `${mediaBase}/api/chat/media/emoji?account=${encodeURIComponent(selectedAccount.value || '')}&md5=${encodeURIComponent(msg.emojiMd5)}&username=${encodeURIComponent(selectedContact.value?.username || '')}` : ''
  const localImageByMd5 = msg.imageMd5 ? `${mediaBase}/api/chat/media/image?account=${encodeURIComponent(selectedAccount.value || '')}&md5=${encodeURIComponent(msg.imageMd5)}&username=${encodeURIComponent(selectedContact.value?.username || '')}` : ''
  const localImageByFileId = msg.imageFileId ? `${mediaBase}/api/chat/media/image?account=${encodeURIComponent(selectedAccount.value || '')}&file_id=${encodeURIComponent(msg.imageFileId)}&username=${encodeURIComponent(selectedContact.value?.username || '')}` : ''
  const normalizedImageUrl = msg.imageUrl || localImageByMd5 || localImageByFileId || ''
  const normalizedEmojiUrl = msg.emojiUrl || localEmojiUrl
  const localVideoThumbUrl = (() => {
    if (!msg.videoThumbMd5 && !msg.videoThumbFileId) return ''
    const parts = [
      `account=${encodeURIComponent(selectedAccount.value || '')}`,
      msg.videoThumbMd5 ? `md5=${encodeURIComponent(msg.videoThumbMd5)}` : '',
      msg.videoThumbFileId ? `file_id=${encodeURIComponent(msg.videoThumbFileId)}` : '',
      `username=${encodeURIComponent(selectedContact.value?.username || '')}`,
    ].filter(Boolean)
    return `${mediaBase}/api/chat/media/video_thumb?${parts.join('&')}`
  })()

  const localVideoUrl = (() => {
    if (!msg.videoMd5 && !msg.videoFileId) return ''
    const parts = [
      `account=${encodeURIComponent(selectedAccount.value || '')}`,
      msg.videoMd5 ? `md5=${encodeURIComponent(msg.videoMd5)}` : '',
      msg.videoFileId ? `file_id=${encodeURIComponent(msg.videoFileId)}` : '',
      `username=${encodeURIComponent(selectedContact.value?.username || '')}`,
    ].filter(Boolean)
    return `${mediaBase}/api/chat/media/video?${parts.join('&')}`
  })()

  const normalizedVideoThumbUrl = (isUsableMediaUrl(msg.videoThumbUrl) ? normalizeMaybeUrl(msg.videoThumbUrl) : '') || localVideoThumbUrl
  const normalizedVideoUrl = (isUsableMediaUrl(msg.videoUrl) ? normalizeMaybeUrl(msg.videoUrl) : '') || localVideoUrl
  const normalizedVoiceUrl = msg.voiceUrl || (msg.serverId ? `${mediaBase}/api/chat/media/voice?account=${encodeURIComponent(selectedAccount.value || '')}&server_id=${encodeURIComponent(String(msg.serverId))}` : '')

  const remoteFromServer = (
    typeof msg.emojiRemoteUrl === 'string'
    && /^https?:\/\//i.test(msg.emojiRemoteUrl)
    && !/\/api\/chat\/media\/emoji\b/i.test(msg.emojiRemoteUrl)
    && !/\blocalhost\b/i.test(msg.emojiRemoteUrl)
    && !/\b127\.0\.0\.1\b/i.test(msg.emojiRemoteUrl)
  ) ? msg.emojiRemoteUrl : ''

  const remoteFromEmojiUrl = (
    typeof msg.emojiUrl === 'string'
    && /^https?:\/\//i.test(msg.emojiUrl)
    && !/\/api\/chat\/media\/emoji\b/i.test(msg.emojiUrl)
    && !/\blocalhost\b/i.test(msg.emojiUrl)
    && !/\b127\.0\.0\.1\b/i.test(msg.emojiUrl)
  ) ? msg.emojiUrl : ''

  const emojiRemoteUrl = remoteFromServer || remoteFromEmojiUrl
  const emojiIsLocal = typeof normalizedEmojiUrl === 'string' && /\/api\/chat\/media\/emoji\b/i.test(normalizedEmojiUrl)
  const emojiDownloaded = !!emojiRemoteUrl && !!emojiIsLocal

  const replyText = String(msg.content || '').trim()
  let quoteContent = String(msg.quoteContent || '')
  const qcTrim = quoteContent.trim()
  if (replyText && qcTrim) {
    if (qcTrim === replyText) {
      quoteContent = ''
    } else {
      const lines = qcTrim.split(/\r?\n/).map((x) => x.trim())
      if (lines.length && (lines[0] === replyText || lines[0] === replyText.split(/\r?\n/)[0]?.trim())) {
        quoteContent = qcTrim.split(/\r?\n/).slice(1).join('\n').trim()
      } else if (qcTrim.startsWith(replyText)) {
        quoteContent = qcTrim.slice(replyText.length).trim()
      }
    }
  }

  return {
    id: msg.id,
    serverId: msg.serverId || 0,
    sender,
    senderUsername: msg.senderUsername || '',
    senderDisplayName: msg.senderDisplayName || '',
    content: msg.content || '',
    time: formatMessageTime(msg.createTime),
    fullTime: formatMessageFullTime(msg.createTime),
    createTime: Number(msg.createTime || 0),
    isSent,
    type: 'text',
    renderType: msg.renderType || 'text',
    voipType: msg.voipType || '',
    title: msg.title || '',
    url: msg.url || '',
    imageMd5: msg.imageMd5 || '',
    imageFileId: msg.imageFileId || '',
    emojiMd5: msg.emojiMd5 || '',
    emojiUrl: normalizedEmojiUrl || '',
    emojiLocalUrl: localEmojiUrl || '',
    emojiRemoteUrl,
    _emojiDownloaded: !!emojiDownloaded,
    thumbUrl: msg.thumbUrl || '',
    imageUrl: normalizedImageUrl || '',
    videoMd5: msg.videoMd5 || '',
    videoThumbMd5: msg.videoThumbMd5 || '',
    videoFileId: msg.videoFileId || '',
    videoThumbFileId: msg.videoThumbFileId || '',
    videoThumbUrl: normalizedVideoThumbUrl || '',
    videoUrl: normalizedVideoUrl || '',
    quoteTitle: msg.quoteTitle || '',
    quoteContent,
    amount: msg.amount || '',
    coverUrl: msg.coverUrl || '',
    fileSize: msg.fileSize || '',
    fileMd5: msg.fileMd5 || '',
    paySubType: msg.paySubType || '',
    transferStatus: msg.transferStatus || '',
    transferReceived: msg.paySubType === '3' || msg.transferStatus === '已收款',
    voiceUrl: normalizedVoiceUrl || '',
    voiceDuration: msg.voiceLength || msg.voiceDuration || '',
    preview: msg.thumbUrl || '',
    from: '',
    isGroup: !!selectedContact.value?.isGroup,
    avatar: msg.senderAvatar || fallbackAvatar || null,
    avatarColor: null
  }
}

const shouldShowEmojiDownload = (message) => {
  if (!message?.emojiMd5) return false
  const u = String(message?.emojiRemoteUrl || '').trim()
  if (!u) return false
  if (!/^https?:\/\//i.test(u)) return false
  return true
}

const onEmojiDownloadClick = async (message) => {
  if (!process.client) return
  if (!message?.emojiMd5) return
  if (!selectedAccount.value) return

  const emojiUrl = String(message?.emojiRemoteUrl || '').trim()
  if (!emojiUrl) {
    window.alert('该表情没有可用的下载地址')
    return
  }

  if (message._emojiDownloading) return
  message._emojiDownloading = true

  try {
    const api = useApi()
    await api.downloadChatEmoji({
      account: selectedAccount.value,
      md5: message.emojiMd5,
      emoji_url: emojiUrl,
      force: false
    })
    message._emojiDownloaded = true
    if (message.emojiLocalUrl) {
      message.emojiUrl = message.emojiLocalUrl
    }
  } catch (e) {
    window.alert(e?.message || '下载失败')
  } finally {
    message._emojiDownloading = false
  }
}

const onGlobalClick = () => {
  if (contextMenu.value.visible) closeContextMenu()
}

onMounted(() => {
  if (!process.client) return
  document.addEventListener('click', onGlobalClick)
})

onUnmounted(() => {
  if (!process.client) return
  document.removeEventListener('click', onGlobalClick)
  stopExportPolling()
})

const loadMessages = async ({ username, reset }) => {
  if (!username) return
  if (!selectedAccount.value) return

  const api = useApi()
  messagesError.value = ''
  isLoadingMessages.value = true
  activeMessagesFor.value = username

  try {
    const existing = allMessages.value[username] || []
    const container = messageContainerRef.value
    const beforeScrollHeight = container ? container.scrollHeight : 0
    const beforeScrollTop = container ? container.scrollTop : 0
    const offset = reset ? 0 : existing.length

    const resp = await api.listChatMessages({
      account: selectedAccount.value,
      username,
      limit: messagePageSize,
      offset,
      order: 'asc'
    })

    const raw = resp?.messages || []
    const mapped = raw.map(normalizeMessage)

    if (activeMessagesFor.value !== username) {
      return
    }

    if (reset) {
      allMessages.value = {
        ...allMessages.value,
        [username]: mapped
      }
    } else {
      allMessages.value = {
        ...allMessages.value,
        [username]: [...mapped, ...existing]
      }
    }

    messagesMeta.value = {
      ...messagesMeta.value,
      [username]: {
        total: Number(resp?.total || 0),
        hasMore: resp?.hasMore
      }
    }

    await nextTick()
    const c = messageContainerRef.value
    if (c) {
      if (reset) {
        c.scrollTop = c.scrollHeight
      } else {
        const afterScrollHeight = c.scrollHeight
        c.scrollTop = beforeScrollTop + (afterScrollHeight - beforeScrollHeight)
      }
    }
  } catch (e) {
    messagesError.value = e?.message || '加载聊天记录失败'
  } finally {
    isLoadingMessages.value = false
  }
}

const loadMoreMessages = async () => {
  if (!selectedContact.value) return
  await loadMessages({ username: selectedContact.value.username, reset: false })
}

const refreshSelectedMessages = async () => {
  if (!selectedContact.value) return
  await loadMessages({ username: selectedContact.value.username, reset: true })
}

watch(
  routeUsername,
  async () => {
    if (isLoadingContacts.value) return
    await applyRouteSelection()
  },
  { immediate: true }
)

const autoLoadReady = ref(true)

const onMessageScroll = async () => {
  const c = messageContainerRef.value
  if (!c) return
  if (!selectedContact.value) return

  if (c.scrollTop > 120) {
    autoLoadReady.value = true
    return
  }

  if (c.scrollTop <= 60 && autoLoadReady.value && hasMoreMessages.value && !isLoadingMessages.value) {
    autoLoadReady.value = false
    await loadMoreMessages()
  }
}

const LinkCard = defineComponent({
  name: 'LinkCard',
  props: {
    href: { type: String, required: true },
    heading: { type: String, default: '' },
    abstract: { type: String, default: '' },
    preview: { type: String, default: '' },
    from: { type: String, default: '' }
  },
  setup(props) {
    return () => h(
      'a',
      {
        href: props.href,
        target: '_blank',
        rel: 'noreferrer',
        class: 'block max-w-sm w-full bg-white msg-radius border border-neutral-200 overflow-hidden hover:bg-gray-50 transition-colors'
      },
      [
        props.preview ? h('div', { class: 'w-full bg-black/5' }, [
          h('img', { src: props.preview, alt: props.heading || '链接预览', class: 'w-full max-h-40 object-cover' })
        ]) : null,
        h('div', { class: 'px-3 py-2' }, [
          h('div', { class: 'text-sm font-medium text-gray-900 line-clamp-2' }, props.heading || props.href),
          props.abstract ? h('div', { class: 'text-xs text-gray-600 mt-1 line-clamp-2' }, props.abstract) : null,
          props.from ? h('div', { class: 'text-[10px] text-gray-400 mt-1 truncate' }, props.from) : null
        ])
      ].filter(Boolean)
    )
  }
})

</script>

<style scoped>
/* 滚动条样式 */
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}

/* 消息气泡样式 */
.message-bubble {
  border-radius: var(--message-radius);
  position: relative;
  z-index: 1;
}

/* 发送的消息（右侧绿色气泡） */
.sent-message {
  background-color: #95EB69 !important;
  border-radius: var(--message-radius);
}

.sent-message::after {
  content: '';
  position: absolute;
  top: 50%;
  right: -4px;
  transform: translateY(-50%) rotate(45deg);
  width: 10px;
  height: 10px;
  background-color: #95EB69;
  border-radius: 2px;
}

/* 接收的消息（左侧白色气泡） */
.received-message {
  background-color: white !important;
  border-radius: var(--message-radius);
}

.received-message::before {
  content: '';
  position: absolute;
  top: 50%;
  left: -4px;
  transform: translateY(-50%) rotate(45deg);
  width: 10px;
  height: 10px;
  background-color: white;
  border-radius: 2px;
}

/* 聊天标签页样式 */
.chat-tab {
  cursor: pointer;
  transition: all 0.2s ease;
  color: #606060;
}

.chat-tab:hover:not(.selected) {
  background-color: #E5E5E5;
}

.chat-tab.selected {
  color: #07b75b !important;
}

.chat-tab:not(.selected):hover {
  color: #07b75b;
}

/* 语音消息样式 */
.voice-message-wrap {
  display: flex;
  width: 100%;
}

.voice-bubble {
  border-radius: var(--message-radius);
  position: relative;
  transition: opacity 0.15s ease;
}

.voice-bubble:hover {
  opacity: 0.85;
}

.voice-bubble:active {
  opacity: 0.7;
}

.voice-sent {
  border-radius: var(--message-radius);
}

.voice-sent::after {
  content: '';
  position: absolute;
  top: 50%;
  right: -4px;
  transform: translateY(-50%) rotate(45deg);
  width: 10px;
  height: 10px;
  background-color: #95EC69;
  border-radius: 2px;
}

.voice-received {
  border-radius: var(--message-radius);
}

.voice-received::before {
  content: '';
  position: absolute;
  top: 50%;
  left: -4px;
  transform: translateY(-50%) rotate(45deg);
  width: 10px;
  height: 10px;
  background-color: white;
  border-radius: 2px;
}

/* 语音消息样式 - 微信风格 */
.wechat-voice-wrapper {
  display: flex;
  width: 100%;
  position: relative;
}

.wechat-voice-bubble {
  border-radius: var(--message-radius);
  position: relative;
  transition: opacity 0.15s ease;
  min-width: 80px;
  max-width: 200px;
}

.wechat-voice-bubble:hover {
  opacity: 0.85;
}

.wechat-voice-bubble:active {
  opacity: 0.7;
}

.wechat-voice-sent {
  background: #95EC69;
}

.wechat-voice-sent::after {
  content: '';
  position: absolute;
  top: 50%;
  right: -4px;
  transform: translateY(-50%) rotate(45deg);
  width: 10px;
  height: 10px;
  background: #95EC69;
  border-radius: 2px;
}

.wechat-voice-received {
  background: white;
}

.wechat-voice-received::before {
  content: '';
  position: absolute;
  top: 50%;
  left: -4px;
  transform: translateY(-50%) rotate(45deg);
  width: 10px;
  height: 10px;
  background: white;
  border-radius: 2px;
}

.wechat-voice-content {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  gap: 8px;
}

/* 语音图标样式 */
.wechat-voice-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  color: #1a1a1a;
}

.voice-icon-sent {
  transform: scaleX(-1);
}

/* 播放时的波动动画 */
.wechat-voice-icon.voice-playing .voice-wave-2 {
  animation: voice-wave-2 1s infinite;
}

.wechat-voice-icon.voice-playing .voice-wave-3 {
  animation: voice-wave-3 1s infinite;
}

@keyframes voice-wave-2 {
  0%, 33% { opacity: 0; }
  34%, 100% { opacity: 1; }
}

@keyframes voice-wave-3 {
  0%, 66% { opacity: 0; }
  67%, 100% { opacity: 1; }
}

.wechat-voice-duration {
  font-size: 14px;
  color: #1a1a1a;
}

.wechat-voice-unread {
  position: absolute;
  top: 50%;
  right: -20px;
  transform: translateY(-50%);
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #e75e58;
}

/* 音视频通话消息样式 - 微信风格 */
.wechat-voip-bubble {
  border-radius: var(--message-radius);
  position: relative;
  min-width: 120px;
}

.wechat-voip-sent {
  background: #95EC69;
}

.wechat-voip-sent::after {
  content: '';
  position: absolute;
  top: 50%;
  right: -4px;
  transform: translateY(-50%) rotate(45deg);
  width: 10px;
  height: 10px;
  background: #95EC69;
  border-radius: 2px;
}

.wechat-voip-received {
  background: white;
}

.wechat-voip-received::before {
  content: '';
  position: absolute;
  top: 50%;
  left: -4px;
  transform: translateY(-50%) rotate(45deg);
  width: 10px;
  height: 10px;
  background: white;
  border-radius: 2px;
}

.wechat-voip-content {
  display: flex;
  align-items: center;
  padding: 8px 14px;
  gap: 8px;
}

.wechat-voip-icon {
  width: 22px;
  height: 14px;
  flex-shrink: 0;
  object-fit: contain;
}

.wechat-voip-text {
  font-size: 14px;
  color: #1a1a1a;
}

/* 统一特殊消息尾巴（红包 / 文件等） */
.wechat-special-card {
  position: relative;
  overflow: visible;
}

.wechat-special-card::after {
  content: '';
  position: absolute;
  top: 16px;
  left: -4px;
  width: 10px;
  height: 10px;
  background-color: inherit;
  transform: rotate(45deg);
  border-radius: 2px;
}

.wechat-special-sent-side::after {
  left: auto;
  right: -4px;
}

/* 转账消息样式 - 微信风格 */
.wechat-transfer-card {
  width: 210px;
  background: #f79c46;
  border-radius: var(--message-radius);
  overflow: visible;
  position: relative;
}

.wechat-transfer-card::after {
  content: '';
  position: absolute;
  top: 16px;
  left: -4px;
  width: 10px;
  height: 10px;
  background: #f79c46;
  transform: rotate(45deg);
  border-radius: 2px;
}

.wechat-transfer-sent-side::after {
  left: auto;
  right: -4px;
}

.wechat-transfer-content {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  min-height: 58px;
}

.wechat-transfer-icon {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  object-fit: contain;
}

.wechat-transfer-info {
  flex: 1;
  margin-left: 10px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.wechat-transfer-amount {
  font-size: 16px;
  font-weight: 500;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.wechat-transfer-status {
  font-size: 12px;
  color: #fff;
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.wechat-transfer-bottom {
  height: 27px;
  display: flex;
  align-items: center;
  padding: 0 12px;
  border-top: none;
  position: relative;
}

.wechat-transfer-bottom::before {
  content: '';
  position: absolute;
  top: 0;
  left: 13px;
  right: 13px;
  height: 1px;
  background: rgba(255,255,255,0.2);
}

.wechat-transfer-bottom span {
  font-size: 11px;
  color: #fff;
}

/* 已领取的转账样式 */
.wechat-transfer-received {
  background: #f8e2c6;
}

.wechat-transfer-received::after {
  background: #f8e2c6;
}

.wechat-transfer-received .wechat-transfer-amount,
.wechat-transfer-received .wechat-transfer-status {
  color: #fff;
}

.wechat-transfer-received .wechat-transfer-bottom span {
  color: #fff;
}

/* 退回的转账样式 */
.wechat-transfer-returned {
  background: #fde1c3;
}

.wechat-transfer-returned::after {
  background: #fde1c3;
}

.wechat-transfer-returned .wechat-transfer-amount,
.wechat-transfer-returned .wechat-transfer-status {
  color: #fff;
}

.wechat-transfer-returned .wechat-transfer-bottom span {
  color: #fff;
}

/* 红包消息样式 - 微信风格 */
.wechat-redpacket-card {
  width: 210px;
  background: #fa9d3b;
  border-radius: var(--message-radius);
  overflow: visible;
  position: relative;
}

.wechat-redpacket-content {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  min-height: 58px;
}

.wechat-redpacket-icon {
  width: 32px;
  height: 36px;
  flex-shrink: 0;
  object-fit: contain;
}

.wechat-redpacket-info {
  flex: 1;
  margin-left: 10px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.wechat-redpacket-text {
  font-size: 14px;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.wechat-redpacket-status {
  font-size: 12px;
  color: #fff;
  margin-top: 2px;
}

.wechat-redpacket-bottom {
  height: 27px;
  display: flex;
  align-items: center;
  padding: 0 12px;
  border-top: none;
  position: relative;
}

.wechat-redpacket-bottom::before {
  content: '';
  position: absolute;
  top: 0;
  left: 13px;
  right: 13px;
  height: 1px;
  background: rgba(255,255,255,0.2);
}

.wechat-redpacket-bottom span {
  font-size: 11px;
  color: #faecda;
}

/* 已领取的红包样式 */
.wechat-redpacket-received {
  background: #f8e2c6;
}

.wechat-redpacket-received .wechat-redpacket-text,
.wechat-redpacket-received .wechat-redpacket-status {
  color: #b88550;
}

.wechat-redpacket-received .wechat-redpacket-bottom span {
  color: #c9a67a;
}

/* 文件消息样式 - 基于红包样式覆盖 */
.wechat-file-card {
  width: 210px;
  background: #fff;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.wechat-file-card .wechat-redpacket-content {
  padding: 10px 12px;
  min-height: 58px;
}

.wechat-file-card .wechat-redpacket-bottom {
  height: 27px;
  padding: 0 12px;
  border-top: none;
  position: relative;
}

.wechat-file-card .wechat-redpacket-bottom::before {
  content: '';
  position: absolute;
  top: 0;
  left: 13px;
  right: 13px;
  height: 1.5px;
  background: #e8e8e8;
}

.wechat-file-card:hover {
  background: #f5f5f5;
}

.wechat-file-card .wechat-file-info {
  margin-left: 0;
  margin-right: 10px;
}

.wechat-file-name {
  font-size: 14px;
  color: #1a1a1a;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-all;
  line-height: 1.4;
}

.wechat-file-size {
  font-size: 12px;
  color: #b2b2b2;
  margin-top: 4px;
}

.wechat-file-icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  object-fit: contain;
}

.wechat-file-bottom {
  border-top: 1px solid #e8e8e8;
}

.wechat-file-bottom span {
  font-size: 12px;
  color: #b2b2b2;
}

.wechat-file-logo {
  width: 18px;
  height: 18px;
  object-fit: contain;
  margin-right: 4px;
}

/* 隐私模式模糊效果 */
.privacy-blur {
  filter: blur(9px);
  transition: filter 0.2s ease;
}

.privacy-blur:hover {
  filter: none;
}
</style>
