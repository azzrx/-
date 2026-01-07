<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

const users = ref([])
const showForm = ref(false)
const isEdit = ref(false)
const searchKeyword = ref('')
const selectedRole = ref('all') // 'all', 'admin', 'teacher', 'student'
const currentUser = ref({
  username: '',
  password: '',
  role: 'admin'
})
const errorMessage = ref('')
const page = ref(1)
const limit = 10
const total = ref(0)

const filteredUsers = computed(() => {
  let result = users.value
  
  // 先按角色筛选
  if (selectedRole.value !== 'all') {
    result = result.filter(user => user.role === selectedRole.value)
  }
  
  // 再按搜索关键词筛选
  if (searchKeyword.value.trim()) {
    const keyword = searchKeyword.value.toLowerCase().trim()
    result = result.filter(user => {
      return (
        (user.username && user.username.toLowerCase().includes(keyword)) ||
        (user.role && user.role.toLowerCase().includes(keyword)) ||
        (user.created_at && user.created_at.includes(keyword))
      )
    })
  }
  
  return result
})

// 统计每种角色的用户数量
const roleCounts = computed(() => {
  return {
    all: users.value.length,
    admin: users.value.filter(u => u.role === 'admin').length,
    teacher: users.value.filter(u => u.role === 'teacher').length,
    student: users.value.filter(u => u.role === 'student').length
  }
})

const fetchUsers = async () => {
  try {
    const response = await axios.get('/api/users', {
      params: { page: page.value, limit }
    })
    users.value = response.data.data || []
    total.value = response.data.total || 0
  } catch (error) {
    console.error('Error fetching users:', error)
    users.value = []
    total.value = 0
  }
}

const changePage = (newPage) => {
  page.value = newPage
  fetchUsers()
}

const totalPages = computed(() => Math.ceil(total.value / limit))

const resetForm = () => {
  currentUser.value = {
    username: '',
    password: '',
    role: 'admin'
  }
  isEdit.value = false
  errorMessage.value = ''
}

const submitForm = async () => {
  try {
    if (isEdit.value) {
      await axios.put(`/api/users/${currentUser.value.id}`, currentUser.value)
    } else {
      await axios.post('/api/users', currentUser.value)
    }
    showForm.value = false
    resetForm()
    await fetchUsers()
  } catch (error) {
    errorMessage.value = error.response?.data?.message || '操作失败'
  }
}

const editUser = (user) => {
  currentUser.value = { ...user, password: '' } // Don't show existing password
  isEdit.value = true
  showForm.value = true
}

const deleteUser = async (id) => {
  if (confirm('确认删除?')) {
    try {
      await axios.delete(`/api/users/${id}`)
      // 如果删除后当前页没有数据，返回上一页
      if (users.value.length === 1 && page.value > 1) {
        page.value--
      }
      await fetchUsers()
    } catch (error) {
      console.error('Error deleting user:', error)
    }
  }
}

onMounted(() => {
  fetchUsers()
})
</script>

<template>
  <div>
    <!-- 角色筛选选项卡 -->
    <div class="role-filter-tabs">
      <button 
        @click="selectedRole = 'all'"
        :class="['role-tab', { 'active': selectedRole === 'all' }]"
      >
        <span class="tab-label">全部</span>
        <span class="tab-count">{{ roleCounts.all }}</span>
      </button>
      <button 
        @click="selectedRole = 'admin'"
        :class="['role-tab', 'role-tab-admin', { 'active': selectedRole === 'admin' }]"
      >
        <span class="tab-label">管理员</span>
        <span class="tab-count">{{ roleCounts.admin }}</span>
      </button>
      <button 
        @click="selectedRole = 'teacher'"
        :class="['role-tab', 'role-tab-teacher', { 'active': selectedRole === 'teacher' }]"
      >
        <span class="tab-label">老师</span>
        <span class="tab-count">{{ roleCounts.teacher }}</span>
      </button>
      <button 
        @click="selectedRole = 'student'"
        :class="['role-tab', 'role-tab-student', { 'active': selectedRole === 'student' }]"
      >
        <span class="tab-label">学生</span>
        <span class="tab-count">{{ roleCounts.student }}</span>
      </button>
    </div>
    
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px; margin-top: 15px;">
      <button @click="showForm = true; resetForm()">添加用户</button>
      <input 
        v-model="searchKeyword" 
        type="text" 
        placeholder="搜索用户（用户名、角色、创建时间）" 
        style="flex: 1; max-width: 400px; padding: 8px; border: 1px solid #ddd; border-radius: 4px;"
      />
      <span v-if="searchKeyword || selectedRole !== 'all'" style="color: #666; font-size: 14px;">
        找到 {{ filteredUsers.length }} 条记录
      </span>
    </div>
    
    <table v-if="filteredUsers.length">
      <thead>
        <tr>
          <th>用户名</th>
          <th>角色</th>
          <th>创建时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr 
          v-for="user in filteredUsers" 
          :key="user.id"
          :class="{
            'admin-row': user.role === 'admin',
            'teacher-row': user.role === 'teacher',
            'student-row': user.role === 'student'
          }"
        >
          <td>
            <span class="username-text">{{ user.username }}</span>
            <span v-if="user.role === 'admin'" class="role-badge admin-badge">管理员</span>
            <span v-else-if="user.role === 'teacher'" class="role-badge teacher-badge">老师</span>
          </td>
          <td>
            <span 
              class="role-label"
              :class="{
                'role-admin': user.role === 'admin',
                'role-teacher': user.role === 'teacher',
                'role-student': user.role === 'student'
              }"
            >
              {{ user.role === 'admin' ? '管理员' : user.role === 'teacher' ? '老师' : '学生' }}
            </span>
          </td>
          <td>{{ user.created_at }}</td>
          <td>
            <button @click="editUser(user)">编辑</button>
            <button @click="deleteUser(user.id)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="!searchKeyword && selectedRole === 'all'">暂无用户</p>
    <p v-else-if="selectedRole !== 'all' && roleCounts[selectedRole] === 0">
      暂无{{ selectedRole === 'admin' ? '管理员' : selectedRole === 'teacher' ? '老师' : '学生' }}用户
    </p>
    <p v-else>未找到匹配的用户</p>

    <div v-if="total > 0 && !searchKeyword && selectedRole === 'all'" class="pagination">
      <button :disabled="page === 1" @click="changePage(page - 1)">上一页</button>
      <span>第 {{ page }} / {{ totalPages }} 页</span>
      <button :disabled="page === totalPages" @click="changePage(page + 1)">下一页</button>
    </div>

    <div v-if="showForm" class="modal">
      <div class="modal-content">
        <h2>{{ isEdit ? '编辑用户' : '添加用户' }}</h2>
        <form @submit.prevent="submitForm">
          <div class="form-group">
            <input v-model="currentUser.username" placeholder="用户名" required :disabled="isEdit" />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">用户名: 唯一用户名</div>
            </div>
          </div>
          <div class="form-group">
            <input v-model="currentUser.password" type="password" :placeholder="isEdit ? '新密码（可选）' : '密码'" :required="!isEdit" />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">密码: 至少6位</div>
            </div>
          </div>
          <div class="form-group">
            <select v-model="currentUser.role" required>
              <option value="admin">管理员</option>
              <option value="teacher">老师</option>
              <option value="student">学生</option>
            </select>
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">角色: 用户权限级别</div>
            </div>
          </div>
          <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
          <div class="buttons">
            <button type="submit">保存</button>
            <button type="button" @click="showForm = false">取消</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
table { width: 100%; border-collapse: collapse; margin-top: 20px; }
th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
button { margin: 5px; }

/* 行高亮样式 */
.admin-row {
  background-color: #fff3e0 !important;
  border-left: 4px solid #ff9800;
  font-weight: 500;
}

.admin-row:hover {
  background-color: #ffe0b2 !important;
}

.teacher-row {
  background-color: #e3f2fd !important;
  border-left: 4px solid #2196f3;
  font-weight: 500;
}

.teacher-row:hover {
  background-color: #bbdefb !important;
}

.student-row {
  background-color: #e8f5e9 !important;
  border-left: 4px solid #4caf50;
  font-weight: 500;
}

.student-row:hover {
  background-color: #c8e6c9 !important;
}

/* 用户名样式 */
.username-text {
  font-weight: 600;
  margin-right: 8px;
}

.admin-row .username-text {
  color: #e65100;
}

.teacher-row .username-text {
  color: #1565c0;
}

.student-row .username-text {
  color: #2e7d32;
}

/* 角色标签样式 */
.role-label {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
  text-align: center;
  min-width: 60px;
}

.role-admin {
  background-color: #ff9800;
  color: white;
}

.role-teacher {
  background-color: #2196f3;
  color: white;
}

.role-student {
  background-color: #4caf50;
  color: white;
}

/* 角色徽章样式 */
.role-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  margin-left: 6px;
  vertical-align: middle;
}

.admin-badge {
  background-color: #ff9800;
  color: white;
}

.teacher-badge {
  background-color: #2196f3;
  color: white;
}
.modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; }
.modal-content { background: linear-gradient(to bottom, #f0f8ff, #ffffff); border: 1px solid #add8e6; padding: 20px; border-radius: 5px; width: 400px; }
form { display: flex; flex-direction: column; }
input, select { margin: 10px 0; padding: 8px; }
.error { color: red; }
.form-group { display: flex; align-items: center; margin-bottom: 10px; }
input, select { flex: 1; background: #f8f8ff; border: 1px solid #b0c4de; padding: 8px; }
.info-container { position: relative; margin-left: 10px; }
.info-ellipsis { cursor: pointer; color: #007bff; font-weight: bold; }
.tooltip { display: none; position: absolute; background: #fff; border: 1px solid #ccc; padding: 5px; border-radius: 3px; white-space: nowrap; top: -30px; left: 0; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
.info-container:hover .tooltip { display: block; }
button[type="submit"], button[type="button"] { 
  width: 100px; 
  height: 62px; 
  border-radius: 5px; 
  cursor: pointer; 
  color: white; 
}
button[type="submit"] { background: #325ecd; }
button[type="button"] { background: #dc3545; }
.buttons { display: flex; justify-content: flex-end; gap: 10px; margin-top: 10px; }

/* 角色筛选选项卡样式 */
.role-filter-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  padding: 10px 0;
  border-bottom: 2px solid #e0e0e0;
}

.role-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  background-color: #f5f5f5;
  color: #666;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  border-bottom: 3px solid transparent;
  margin-bottom: -12px;
}

.role-tab:hover {
  background-color: #e8e8e8;
  transform: translateY(-2px);
}

.role-tab.active {
  background-color: #fff;
  color: #333;
  font-weight: 600;
  border-bottom-color: #2196f3;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.role-tab-admin.active {
  border-bottom-color: #ff9800;
}

.role-tab-teacher.active {
  border-bottom-color: #2196f3;
}

.role-tab-student.active {
  border-bottom-color: #4caf50;
}

.tab-label {
  font-size: 14px;
}

.tab-count {
  background-color: rgba(0, 0, 0, 0.1);
  color: inherit;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  min-width: 24px;
  text-align: center;
}

.role-tab.active .tab-count {
  background-color: rgba(33, 150, 243, 0.2);
  color: #2196f3;
}

.role-tab-admin.active .tab-count {
  background-color: rgba(255, 152, 0, 0.2);
  color: #ff9800;
}

.role-tab-teacher.active .tab-count {
  background-color: rgba(33, 150, 243, 0.2);
  color: #2196f3;
}

.role-tab-student.active .tab-count {
  background-color: rgba(76, 175, 80, 0.2);
  color: #4caf50;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  margin-top: 20px;
  padding: 15px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.pagination button {
  padding: 10px 20px;
  background: linear-gradient(135deg, #607d8b 0%, #455a64 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
}

.pagination button:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(96, 125, 139, 0.4);
  transform: translateY(-2px);
}

.pagination button:disabled {
  background: #e0e0e0;
  color: #999;
  cursor: not-allowed;
  opacity: 0.6;
}

.pagination span {
  color: #607d8b;
  font-weight: 500;
}
</style>

