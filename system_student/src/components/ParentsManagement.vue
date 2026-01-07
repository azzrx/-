<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

const props = defineProps({
  readonly: {
    type: Boolean,
    default: false
  },
  studentId: {
    type: String,
    default: null
  }
})

const students = ref([])
const parents = ref([])
const showForm = ref(false)
const isEdit = ref(false)
const searchKeyword = ref('')
const currentParent = ref({
  student_id: '',
  parent_name: '',
  relationship: '',
  phone: '',
  email: '',
  address: ''
})
const errorMessage = ref('')
const page = ref(1)
const limit = 10
const total = ref(0)

const filteredParents = computed(() => {
  // 如果是只读模式，确保只显示当前学生的家长信息
  let filtered = parents.value
  if (props.readonly && props.studentId) {
    filtered = filtered.filter(p => {
      const studentId = p.student_id || p.studentId
      return studentId === props.studentId
    })
  }
  
  if (!searchKeyword.value.trim()) {
    return filtered
  }
  
  const keyword = searchKeyword.value.toLowerCase().trim()
  return filtered.filter(p => {
    return (
      (p.student_name && p.student_name.toLowerCase().includes(keyword)) ||
      (p.student_id && p.student_id.toLowerCase().includes(keyword)) ||
      (p.parent_name && p.parent_name.toLowerCase().includes(keyword)) ||
      (p.relationship && p.relationship.toLowerCase().includes(keyword)) ||
      (p.phone && p.phone.toLowerCase().includes(keyword)) ||
      (p.email && p.email.toLowerCase().includes(keyword)) ||
      (p.address && p.address.toLowerCase().includes(keyword))
    )
  })
})

const fetchStudents = async () => {
  try {
    // 获取所有学生（不分页，用于下拉选择）
    const response = await axios.get('/api/students', {
      params: { page: 1, limit: 1000 }
    })
    students.value = response.data.data || response.data || []
  } catch (error) {
    console.error('Error fetching students:', error)
    students.value = []
  }
}

const fetchParents = async () => {
  try {
    let response
    if (props.readonly && props.studentId) {
      // 学生角色：只获取自己的家长信息（不分页，获取所有）
      response = await axios.get('/api/parents', {
        params: { student_id: props.studentId, page: 1, limit: 1000 }
      })
    } else {
      // 管理员角色：获取所有家长信息（分页）
      response = await axios.get('/api/parents', {
        params: { page: page.value, limit }
      })
    }
    
    const data = response.data.data || response.data || []
    parents.value = Array.isArray(data) ? data : []
    total.value = response.data.total || parents.value.length
    
    // 如果是只读模式，再次过滤确保只包含当前学生的数据
    if (props.readonly && props.studentId) {
      parents.value = parents.value.filter(p => {
        const studentId = p.student_id || p.studentId
        return studentId === props.studentId
      })
      total.value = parents.value.length
    }
  } catch (error) {
    console.error('Error fetching parents:', error)
    parents.value = []
    total.value = 0
  }
}

const changePage = (newPage) => {
  page.value = newPage
  fetchParents()
}

const totalPages = computed(() => Math.ceil(total.value / limit))

const resetForm = () => {
  currentParent.value = {
    student_id: props.readonly && props.studentId ? props.studentId : '',
    parent_name: '',
    relationship: '',
    phone: '',
    email: '',
    address: ''
  }
  isEdit.value = false
  errorMessage.value = ''
}

const submitForm = async () => {
  // 如果是学生模式，确保只能编辑自己的家长信息
  if (props.readonly && props.studentId) {
    if (isEdit.value) {
      // 编辑时，确保student_id是当前学生的ID
      if (currentParent.value.student_id !== props.studentId) {
        alert('您只能编辑自己的家长信息')
        return
      }
      // 强制使用当前学生的ID
      currentParent.value.student_id = props.studentId
    } else {
      // 添加时，强制使用当前学生的ID
      currentParent.value.student_id = props.studentId
    }
  }
  
  try {
    if (isEdit.value) {
      const response = await axios.put(`/api/parents/${currentParent.value.id}`, currentParent.value)
      if (response.data.success) {
        alert('家长信息更新成功')
      }
    } else {
      const response = await axios.post('/api/parents', currentParent.value)
      if (response.data.success) {
        alert('家长信息添加成功')
      }
    }
    showForm.value = false
    resetForm()
    await fetchParents()
  } catch (error) {
    console.error('Submit error:', error)
    errorMessage.value = error.response?.data?.message || '操作失败'
    alert(errorMessage.value)
  }
}

const editParent = (p) => {
  // 如果是只读模式，检查是否可以编辑
  if (props.readonly && props.studentId) {
    const studentId = p.student_id || p.studentId
    if (studentId !== props.studentId) {
      alert('您只能编辑自己的家长信息')
      return
    }
  }
  currentParent.value = { ...p }
  isEdit.value = true
  showForm.value = true
}

const deleteParent = async (id) => {
  // 学生模式下不允许删除
  if (props.readonly) {
    alert('学生无权删除家长信息')
    return
  }
  if (confirm('确认删除?')) {
    try {
      await axios.delete(`/api/parents/${id}`)
      // 如果删除后当前页没有数据，返回上一页
      if (parents.value.length === 1 && page.value > 1) {
        page.value--
      }
      await fetchParents()
    } catch (error) {
      console.error('Error deleting parent:', error)
    }
  }
}

const sendNotification = async (parent) => {
  // Simulated notification send
  alert(`模拟发送通知给 ${parent.parent_name} (${parent.phone})`)
  // In real app, call backend API for SMS/email
}

onMounted(() => {
  if (!props.readonly) {
    fetchStudents()  // 学生模式下不需要获取所有学生列表
  }
  fetchParents()
})
</script>

<template>
  <div>
    <div v-if="!readonly" class="toolbar">
      <button @click="showForm = true; resetForm()" class="add-button-purple">
        <span style="margin-right: 6px;">➕</span>添加家长
      </button>
      <div class="search-container">
        <input 
          v-model="searchKeyword" 
          type="text" 
          placeholder="🔍 搜索家长（学生姓名、学号、家长姓名、关系、电话、邮箱、地址）" 
          class="search-input"
        />
        <span v-if="searchKeyword" class="search-result">
          找到 {{ filteredParents.length }} 条记录
        </span>
      </div>
    </div>
    <div v-else class="readonly-header">
      <h3 class="section-title-purple">👨‍👩‍👧 我的家长信息</h3>
      <p v-if="!props.studentId" class="info-hint">提示：未找到对应的学生信息，请联系管理员</p>
      <p v-else class="info-description">您可以查看和编辑自己的家长信息</p>
      <div class="toolbar">
        <button @click="showForm = true; resetForm()" class="add-button-purple">添加家长</button>
        <div class="search-container">
          <input 
            v-model="searchKeyword" 
            type="text" 
            placeholder="🔍 搜索家长（家长姓名、关系、电话、邮箱、地址）" 
            class="search-input"
          />
          <span v-if="searchKeyword" class="search-result">
            找到 {{ filteredParents.length }} 条记录
          </span>
        </div>
      </div>
    </div>
    
    <table v-if="filteredParents.length">
      <thead>
        <tr>
          <th v-if="!readonly">学生姓名</th>
          <th>家长姓名</th>
          <th>关系</th>
          <th>电话</th>
          <th>邮箱</th>
          <th>地址</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="p in filteredParents" :key="p.id">
          <td v-if="!readonly">{{ p.student_name }}</td>
          <td>{{ p.parent_name }}</td>
          <td>{{ p.relationship }}</td>
          <td>{{ p.phone }}</td>
          <td>{{ p.email }}</td>
          <td>{{ p.address }}</td>
          <td>
            <button @click="editParent(p)">编辑</button>
            <button v-if="!readonly" @click="deleteParent(p.id)">删除</button>
            <button v-if="!readonly" @click="sendNotification(p)" class="notify-button">发送通知</button>
            <span v-if="readonly" class="no-delete-hint">无法删除</span>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="!searchKeyword">暂无家长信息</p>
    <p v-else>未找到匹配的家长信息</p>

    <div v-if="total > 0 && !searchKeyword && !readonly" class="pagination">
      <button :disabled="page === 1" @click="changePage(page - 1)">上一页</button>
      <span>第 {{ page }} / {{ totalPages }} 页</span>
      <button :disabled="page === totalPages" @click="changePage(page + 1)">下一页</button>
    </div>

    <div v-if="showForm" class="modal">
      <div class="modal-content">
        <h2>{{ isEdit ? '编辑家长' : '添加家长' }}</h2>
        <form @submit.prevent="submitForm">
          <div class="form-group" v-if="!readonly">
            <select v-model="currentParent.student_id" required>
              <option value="">选择学生</option>
              <option v-for="student in students" :key="student.student_id" :value="student.student_id">{{ student.name }}</option>
            </select>
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">学生: 选择一位学生</div>
            </div>
          </div>
          <div class="form-group" v-else>
            <input :value="'学生: ' + (students.find(s => s.student_id === props.studentId)?.name || '我')" disabled style="background-color: #e9ecef;" />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">学生: 当前登录学生（不可修改）</div>
            </div>
          </div>
          <div class="form-group">
            <input v-model="currentParent.parent_name" placeholder="家长姓名" required />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">家长姓名</div>
            </div>
          </div>
          <div class="form-group">
            <select v-model="currentParent.relationship" required>
              <option value="">选择关系</option>
              <option value="父亲">父亲</option>
              <option value="母亲">母亲</option>
            </select>
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">关系: 父亲/母亲</div>
            </div>
          </div>
          <div class="form-group">
            <input v-model="currentParent.phone" placeholder="电话" required />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">电话: 联系电话</div>
            </div>
          </div>
          <div class="form-group">
            <input v-model="currentParent.email" placeholder="邮箱" />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">邮箱: email 地址</div>
            </div>
          </div>
          <div class="form-group">
            <input v-model="currentParent.address" placeholder="地址" />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">地址: （选填）家庭地址</div>
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
/* 紫色主题 - 家长联系 */
/* 主表格样式 */
table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  margin-top: 20px;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

th {
  background: linear-gradient(135deg, #9c27b0 0%, #7b1fa2 100%);
  color: white;
  padding: 16px 12px;
  text-align: left;
  font-weight: 600;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border: none;
  position: sticky;
  top: 0;
  z-index: 10;
}

td {
  padding: 14px 12px;
  border-bottom: 1px solid #f0f0f0;
  color: #333;
  font-size: 14px;
  transition: background-color 0.2s ease;
}

tbody tr {
  transition: all 0.2s ease;
}

tbody tr:hover {
  background-color: #f3e5f5;
  transform: scale(1.001);
  box-shadow: 0 2px 8px rgba(156, 39, 176, 0.1);
}

tbody tr:last-child td {
  border-bottom: none;
}

/* 按钮样式 */
button {
  margin: 0 4px;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

td button:first-of-type {
  background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
  color: white;
}

td button:nth-of-type(2) {
  background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
  color: white;
}

.notify-button {
  background: linear-gradient(135deg, #9c27b0 0%, #7b1fa2 100%);
  color: white;
}

.notify-button:hover {
  box-shadow: 0 4px 12px rgba(156, 39, 176, 0.4);
}

.no-delete-hint {
  color: #999;
  margin-left: 12px;
  font-size: 13px;
  font-style: italic;
}

/* 工具栏 */
.toolbar, .readonly-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.readonly-header {
  flex-direction: column;
  align-items: flex-start;
}

.add-button-purple {
  background: linear-gradient(135deg, #9c27b0 0%, #7b1fa2 100%);
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  white-space: nowrap;
}

.add-button-purple:hover {
  box-shadow: 0 4px 12px rgba(156, 39, 176, 0.4);
}

.search-container {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.search-input {
  flex: 1;
  max-width: 500px;
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
  background: white;
}

.search-input:focus {
  outline: none;
  border-color: #9c27b0;
  box-shadow: 0 0 0 3px rgba(156, 39, 176, 0.1);
}

.search-result {
  color: #9c27b0;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
}

.section-title-purple {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 22px;
  font-weight: 600;
  background: linear-gradient(135deg, #9c27b0 0%, #7b1fa2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.info-hint {
  color: #9c27b0;
  font-size: 14px;
  margin: 8px 0 0 0;
  padding: 10px;
  background: #f3e5f5;
  border-radius: 6px;
  border-left: 4px solid #9c27b0;
}

.info-description {
  color: #666;
  font-size: 13px;
  margin: 8px 0 0 0;
}

/* 模态框 */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: white;
  border: none;
  padding: 30px;
  border-radius: 16px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: modalFadeIn 0.3s ease-out;
}

@keyframes modalFadeIn {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.modal-content h2 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 24px;
  background: linear-gradient(135deg, #9c27b0 0%, #7b1fa2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

form {
  display: flex;
  flex-direction: column;
}

.form-group {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
  position: relative;
}

input, select {
  flex: 1;
  background: #f8f9fa;
  border: 2px solid #e0e0e0;
  padding: 12px;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
}

input:focus, select:focus {
  outline: none;
  border-color: #9c27b0;
  background: white;
  box-shadow: 0 0 0 3px rgba(156, 39, 176, 0.1);
}

.info-container {
  position: relative;
  margin-left: 10px;
}

.info-ellipsis {
  cursor: pointer;
  color: #9c27b0;
  font-weight: bold;
  font-size: 18px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #f3e5f5;
  transition: all 0.3s ease;
}

.info-ellipsis:hover {
  background: #9c27b0;
  color: white;
  transform: scale(1.1);
}

.tooltip {
  display: none;
  position: absolute;
  background: #333;
  color: white;
  padding: 8px 12px;
  border-radius: 6px;
  white-space: nowrap;
  top: -40px;
  left: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  font-size: 12px;
  z-index: 100;
}

.tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 20px;
  border: 6px solid transparent;
  border-top-color: #333;
}

.info-container:hover .tooltip {
  display: block;
}

button[type="submit"], button[type="button"] {
  width: 120px;
  height: 44px;
  border-radius: 8px;
  cursor: pointer;
  color: white;
  font-size: 14px;
  font-weight: 600;
}

button[type="submit"] {
  background: linear-gradient(135deg, #9c27b0 0%, #7b1fa2 100%);
}

button[type="submit"]:hover {
  box-shadow: 0 4px 12px rgba(156, 39, 176, 0.4);
}

button[type="button"] {
  background: linear-gradient(135deg, #9e9e9e 0%, #757575 100%);
}

.error {
  color: #f44336;
  background: #ffebee;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 15px;
  border-left: 4px solid #f44336;
}

.buttons {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

p[style*="color: #999"] {
  text-align: center;
  padding: 40px 20px;
  color: #999;
  font-size: 15px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
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
  background: linear-gradient(135deg, #9c27b0 0%, #7b1fa2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
}

.pagination button:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(156, 39, 176, 0.4);
  transform: translateY(-2px);
}

.pagination button:disabled {
  background: #e0e0e0;
  color: #999;
  cursor: not-allowed;
  opacity: 0.6;
}

.pagination span {
  color: #9c27b0;
  font-weight: 500;
}
</style>

