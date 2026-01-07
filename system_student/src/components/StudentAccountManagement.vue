<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const props = defineProps({
  userId: {
    type: Number,
    required: true
  },
  username: {
    type: String,
    required: true
  }
})

const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const showForm = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const resetForm = () => {
  oldPassword.value = ''
  newPassword.value = ''
  confirmPassword.value = ''
  errorMessage.value = ''
  successMessage.value = ''
}

const validatePassword = () => {
  if (!oldPassword.value) {
    errorMessage.value = '请输入当前密码'
    return false
  }
  
  if (!newPassword.value) {
    errorMessage.value = '请输入新密码'
    return false
  }
  
  if (newPassword.value.length < 6) {
    errorMessage.value = '新密码长度至少为6位'
    return false
  }
  
  if (newPassword.value !== confirmPassword.value) {
    errorMessage.value = '两次输入的新密码不一致'
    return false
  }
  
  if (oldPassword.value === newPassword.value) {
    errorMessage.value = '新密码不能与当前密码相同'
    return false
  }
  
  return true
}

const changePassword = async () => {
  errorMessage.value = ''
  successMessage.value = ''
  
  if (!validatePassword()) {
    return
  }
  
  try {
    // 首先验证当前密码是否正确
    const verifyResponse = await axios.post('/api/login', {
      username: props.username,
      password: oldPassword.value
    })
    
    if (!verifyResponse.data.success) {
      errorMessage.value = '当前密码不正确'
      return
    }
    
    // 验证通过后，更新密码（不发送role字段，保持原有角色）
    const updateResponse = await axios.put(`/api/users/${props.userId}`, {
      password: newPassword.value
    })
    
    if (updateResponse.data.success) {
      successMessage.value = '密码修改成功，请重新登录'
      resetForm()
      showForm.value = false
      // 延迟后提示用户重新登录
      setTimeout(() => {
        alert('密码已修改，请重新登录')
        window.location.reload()
      }, 1000)
    } else {
      errorMessage.value = updateResponse.data.message || '密码修改失败'
    }
  } catch (error) {
    if (error.response?.status === 400 || error.response?.status === 401) {
      errorMessage.value = error.response?.data?.message || '当前密码不正确'
    } else {
      errorMessage.value = error.response?.data?.message || '密码修改失败，请稍后重试'
    }
    console.error('Error changing password:', error)
  }
}

onMounted(() => {
  // 组件挂载时不做特殊操作
})
</script>

<template>
  <div class="account-management">
    <h2 class="page-title">账户管理</h2>
    <p class="description">您可以修改自己的登录密码</p>
    
    <div class="info-card">
      <div class="info-item">
        <span class="info-label">用户名：</span>
        <span class="info-value">{{ username }}</span>
      </div>
    </div>
    
    <div class="action-section">
      <button @click="showForm = true; resetForm()" class="btn-change-password">
        修改密码
      </button>
    </div>
    
    <!-- 修改密码表单 -->
    <div v-if="showForm" class="modal" @click.self="showForm = false">
      <div class="modal-content" @click.stop>
        <h3>修改密码</h3>
        <form @submit.prevent="changePassword">
          <div class="form-group">
            <label>当前密码：</label>
            <input 
              v-model="oldPassword" 
              type="password" 
              placeholder="请输入当前密码"
              required
              class="form-input"
            />
          </div>
          
          <div class="form-group">
            <label>新密码：</label>
            <input 
              v-model="newPassword" 
              type="password" 
              placeholder="请输入新密码（至少6位）"
              required
              class="form-input"
            />
            <small class="form-hint">密码长度至少为6位</small>
          </div>
          
          <div class="form-group">
            <label>确认新密码：</label>
            <input 
              v-model="confirmPassword" 
              type="password" 
              placeholder="请再次输入新密码"
              required
              class="form-input"
            />
          </div>
          
          <div v-if="errorMessage" class="error-message">
            {{ errorMessage }}
          </div>
          
          <div v-if="successMessage" class="success-message">
            {{ successMessage }}
          </div>
          
          <div class="form-actions">
            <button type="submit" class="btn-submit">确认修改</button>
            <button type="button" @click="showForm = false; resetForm()" class="btn-cancel">取消</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.account-management {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.page-title {
  font-size: 24px;
  font-weight: bold;
  color: #333;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 2px solid #4caf50;
}

.description {
  color: #666;
  margin-bottom: 30px;
  font-size: 14px;
}

.info-card {
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 30px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.info-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.info-label {
  font-weight: 600;
  color: #2e7d32;
  font-size: 16px;
}

.info-value {
  font-size: 16px;
  color: #1b5e20;
  font-weight: 500;
}

.action-section {
  margin-bottom: 30px;
  display: flex;
  justify-content: flex-end;
}

.btn-change-password {
  background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
  color: white;
  border: none;
  padding: 12px 30px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(76, 175, 80, 0.3);
}

.btn-change-password:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(76, 175, 80, 0.4);
  background: linear-gradient(135deg, #45a049 0%, #4caf50 100%);
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 30px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.modal-content h3 {
  margin: 0 0 20px 0;
  font-size: 20px;
  color: #333;
  text-align: center;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #555;
  font-weight: 500;
  font-size: 14px;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.3s ease;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #4caf50;
}

.form-hint {
  display: block;
  margin-top: 5px;
  color: #999;
  font-size: 12px;
}

.error-message {
  background-color: #ffebee;
  color: #c62828;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 15px;
  font-size: 14px;
  border-left: 4px solid #c62828;
}

.success-message {
  background-color: #e8f5e9;
  color: #2e7d32;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 15px;
  font-size: 14px;
  border-left: 4px solid #4caf50;
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

.btn-submit {
  background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-submit:hover {
  background: linear-gradient(135deg, #45a049 0%, #4caf50 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(76, 175, 80, 0.3);
}

.btn-cancel {
  background: #f5f5f5;
  color: #666;
  border: none;
  padding: 10px 24px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-cancel:hover {
  background: #e0e0e0;
}
</style>

