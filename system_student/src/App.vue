<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import StudentManagement from './components/StudentManagement.vue'
import CourseManagement from './components/CourseManagement.vue'
import StudentCourseManagement from './components/StudentCourseManagement.vue'
import AttendanceManagement from './components/AttendanceManagement.vue'
import RewardsManagement from './components/RewardsManagement.vue'
import ParentsManagement from './components/ParentsManagement.vue'
import UsersManagement from './components/UsersManagement.vue'
import Statistics from './components/Statistics.vue'
import StudentAccountManagement from './components/StudentAccountManagement.vue'

const activeTab = ref('students')
const userRole = ref(null)
const studentId = ref(null)
const userId = ref(null)
const currentUsername = ref(null)
const username = ref('')
const password = ref('')
const loginError = ref('')

// 应用启动时清除登录状态，强制显示登录界面
onMounted(() => {
  logout()
})

const systemTitle = computed(() => {
  if (userRole.value === 'student') {
    return '学生系统'
  } else if (userRole.value === 'teacher') {
    return '老师系统'
  } else if (userRole.value === 'admin') {
    return '学生管理系统'
  }
  return '学生管理系统'
})

const login = async () => {
  try {
    const response = await axios.post('/api/login', { username: username.value, password: password.value })
    if (response.data.success) {
      userRole.value = response.data.user.role
      localStorage.setItem('userRole', userRole.value)
      if (response.data.user.id) {
        userId.value = response.data.user.id
        localStorage.setItem('userId', userId.value.toString())
      }
      if (response.data.user.username) {
        currentUsername.value = response.data.user.username
        localStorage.setItem('username', currentUsername.value)
      }
      if (response.data.user.student_id) {
        studentId.value = response.data.user.student_id
        localStorage.setItem('studentId', studentId.value)
      }
      loginError.value = ''
    } else {
      loginError.value = '登录失败'
    }
  } catch (error) {
    loginError.value = '网络错误'
  }
}

const logout = () => {
  userRole.value = null
  studentId.value = null
  userId.value = null
  currentUsername.value = null
  localStorage.removeItem('userRole')
  localStorage.removeItem('studentId')
  localStorage.removeItem('userId')
  localStorage.removeItem('username')
}

const getTabs = () => {
  if (userRole.value === 'admin') {
    return ['students', 'courses', 'studentCourses', 'attendance', 'rewards', 'parents', 'statistics', 'users']
  } else if (userRole.value === 'teacher') {
    return ['studentCourses', 'attendance', 'rewards', 'parents', 'statistics', 'users']
  } else if (userRole.value === 'student') {
    return ['students', 'courses', 'studentCourses', 'parents', 'account']
  }
  return []
}

const fillStudentAccount = () => {
  username.value = 'student'
  password.value = 'student123'
}
</script>
<template>
  <div class="container">
    <div v-if="!userRole">
      <h1 class="title">登录</h1>
      <form @submit.prevent="login" class="login-form">
        <input v-model="username" placeholder="用户名" required class="input" />
        <input v-model="password" type="password" placeholder="密码" required class="input" />
        <button type="submit" class="button primary">登录</button>
        <p v-if="loginError" class="error">{{ loginError }}</p>
      </form>
      
      <!-- 默认账号提示 -->
      <div class="account-info">
        <div class="info-header">
          <span class="info-icon">ℹ️</span>
          <span class="info-title">学生账号信息</span>
        </div>
        <div class="account-list">
          <div class="account-item student-account">
            <div class="account-label">👨‍🎓 学生账号：</div>
            <div class="account-detail">
              <span class="account-text">用户名：<strong>student</strong></span>
              <span class="account-text">密码：<strong>student123</strong></span>
            </div>
            <button @click="fillStudentAccount" class="quick-fill-btn">快速填入</button>
          </div>
        </div>
        <div class="info-note">
          <p>💡 提示：新学生可以使用任意用户名，密码为 <strong>123456</strong> 自动注册</p>
        </div>
      </div>
    </div>
    <div v-else class="main-container">
      <div class="header-section">
        <div class="title-container">
          <h1 class="title">{{ systemTitle }}</h1>
          <div class="role-badge" :class="'role-' + userRole">
            {{ userRole === 'admin' ? '管理员' : userRole === 'teacher' ? '老师' : '学生' }}
          </div>
        </div>
        <button @click="logout" class="button logout">退出登录</button>
      </div>
      <div class="tabs">
        <button v-for="tab in getTabs()" :key="tab" class="tab" :class="{ active: activeTab === tab }" @click="activeTab = tab">
          {{ tab === 'students' ? '学生管理' : tab === 'courses' ? '课程管理' : tab === 'studentCourses' ? '选课管理' : tab === 'attendance' ? '考勤管理' : tab === 'rewards' ? '奖励处分' : tab === 'parents' ? '家长联系' : tab === 'statistics' ? '系统统计' : tab === 'account' ? '账户管理' : '用户管理' }}
        </button>
      </div>
      <StudentManagement v-if="activeTab === 'students'" :readonly="userRole === 'student'" :studentId="userRole === 'student' ? studentId : null" />
      <CourseManagement v-if="activeTab === 'courses'" :readonly="userRole === 'student'" />
      <StudentCourseManagement v-if="activeTab === 'studentCourses'" :readonly="userRole === 'student'" :studentId="userRole === 'student' ? studentId : null" />
      <AttendanceManagement v-if="activeTab === 'attendance'" />
      <RewardsManagement v-if="activeTab === 'rewards'" />
      <ParentsManagement v-if="activeTab === 'parents'" :readonly="userRole === 'student'" :studentId="userRole === 'student' ? studentId : null" />
      <Statistics v-if="activeTab === 'statistics'" />
      <UsersManagement v-if="activeTab === 'users'" />
      <StudentAccountManagement v-if="activeTab === 'account' && userRole === 'student' && userId && currentUsername" :userId="userId" :username="currentUsername" />
    </div>
  </div>
</template>

<style scoped>
.container { 
  max-width: 1400px; 
  margin: 0 auto; 
  padding: 20px;
  min-height: 100vh;
  background: linear-gradient(to bottom, #f5f7fa 0%, #ffffff 100%);
}

.main-container {
  background: transparent;
}

/* 登录表单样式 */
.login-form { 
  max-width: 400px; 
  margin: 40px auto; 
  display: flex; 
  flex-direction: column; 
  gap: 15px;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.title { 
  text-align: center; 
  font-size: 32px; 
  font-weight: bold; 
  margin: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.input { 
  padding: 12px 16px; 
  border: 2px solid #e0e0e0; 
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.3s ease;
}

.input:focus {
  outline: none;
  border-color: #667eea;
}

.error { 
  color: #dc3545; 
  text-align: center;
  padding: 10px;
  background: #ffebee;
  border-radius: 6px;
  font-size: 14px;
}

/* 账号信息卡片样式 */
.account-info {
  max-width: 400px;
  margin: 30px auto;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.info-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 15px;
  padding-bottom: 12px;
  border-bottom: 2px solid #f0f0f0;
}

.info-icon {
  font-size: 20px;
}

.info-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.account-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 15px;
}

.account-item {
  padding: 12px;
  border-radius: 8px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;
}

.account-item.student-account {
  background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%);
  border: 2px solid #4caf50;
  box-shadow: 0 2px 8px rgba(76, 175, 80, 0.2);
}

.account-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.account-label {
  font-size: 14px;
  font-weight: 600;
  color: #555;
  margin-bottom: 8px;
}

.account-detail {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.account-text {
  font-size: 13px;
  color: #666;
}

.account-text strong {
  color: #667eea;
  font-weight: 600;
}

.student-account .account-text strong {
  color: #4caf50;
}

.quick-fill-btn {
  margin-top: 10px;
  padding: 6px 16px;
  background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  width: 100%;
}

.quick-fill-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
}


.info-note {
  padding: 12px;
  background: #fff3cd;
  border-radius: 8px;
  border-left: 4px solid #ffc107;
}

.info-note p {
  margin: 0;
  font-size: 13px;
  color: #856404;
  line-height: 1.5;
}

.info-note strong {
  color: #d68910;
  font-weight: 600;
}

/* 头部区域样式 */
.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px 30px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.title-container {
  display: flex;
  align-items: center;
  gap: 15px;
}

.title-container .title {
  margin: 0;
  font-size: 28px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.role-badge {
  display: inline-block;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  color: white;
}

.role-badge.role-admin {
  background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
}

.role-badge.role-teacher {
  background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
}

.role-badge.role-student {
  background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
}

/* 标签页样式 */
.tabs { 
  display: flex; 
  justify-content: center; 
  gap: 8px; 
  margin-bottom: 30px; 
  flex-wrap: wrap;
  padding: 0 20px;
}

.tab { 
  padding: 12px 24px; 
  border-radius: 8px; 
  cursor: pointer; 
  transition: all 0.3s ease; 
  background-color: white;
  color: #555;
  border: 2px solid #e0e0e0;
  font-size: 14px;
  font-weight: 500;
}

.tab:hover { 
  background-color: #f5f5f5;
  border-color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.2);
}

.tab.active { 
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

/* 按钮样式 */
.button { 
  padding: 10px 20px; 
  border-radius: 8px; 
  cursor: pointer;
  border: none;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.button.primary { 
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.button.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}

.button.logout { 
  background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);
}

.button.logout:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(220, 53, 69, 0.4);
}

@media (max-width: 768px) {
  .header-section {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
  
  .title-container {
    width: 100%;
    justify-content: space-between;
  }
  
  .title-container .title {
    font-size: 24px;
  }
  
  .button.logout {
    width: 100%;
  }
  
  .tabs {
    justify-content: flex-start;
    overflow-x: auto;
    padding: 0 10px;
  }
}
</style>