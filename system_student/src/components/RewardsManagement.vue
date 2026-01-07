<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

const students = ref([])
const rewards = ref([])
const showForm = ref(false)
const isEdit = ref(false)
const searchKeyword = ref('')
const currentReward = ref({
  student_id: '',
  type: '',
  title: '',
  description: '',
  date: ''
})
const errorMessage = ref('')
const page = ref(1)
const limit = 10
const total = ref(0)

const filteredRewards = computed(() => {
  if (!searchKeyword.value.trim()) {
    return rewards.value
  }
  const keyword = searchKeyword.value.toLowerCase().trim()
  return rewards.value.filter(rp => {
    return (
      (rp.student_name && rp.student_name.toLowerCase().includes(keyword)) ||
      (rp.student_id && rp.student_id.toLowerCase().includes(keyword)) ||
      (rp.type && rp.type.toLowerCase().includes(keyword)) ||
      (rp.title && rp.title.toLowerCase().includes(keyword)) ||
      (rp.description && rp.description.toLowerCase().includes(keyword)) ||
      (rp.date && rp.date.includes(keyword))
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

const fetchRewards = async () => {
  try {
    const response = await axios.get('/api/rewards-punishments', {
      params: { page: page.value, limit }
    })
    rewards.value = response.data.data || []
    total.value = response.data.total || 0
  } catch (error) {
    console.error('Error fetching rewards:', error)
    rewards.value = []
    total.value = 0
  }
}

const changePage = (newPage) => {
  page.value = newPage
  fetchRewards()
}

const totalPages = computed(() => Math.ceil(total.value / limit))

const resetForm = () => {
  currentReward.value = {
    student_id: '',
    type: '',
    title: '',
    description: '',
    date: ''
  }
  isEdit.value = false
  errorMessage.value = ''
}

const submitForm = async () => {
  try {
    if (isEdit.value) {
      await axios.put(`/api/rewards-punishments/${currentReward.value.id}`, currentReward.value)
    } else {
      await axios.post('/api/rewards-punishments', currentReward.value)
    }
    showForm.value = false
    resetForm()
    await fetchRewards()
  } catch (error) {
    errorMessage.value = error.response?.data?.message || '操作失败'
  }
}

const editReward = (rp) => {
  currentReward.value = { ...rp }
  isEdit.value = true
  showForm.value = true
}

const deleteReward = async (id) => {
  if (confirm('确认删除?')) {
    try {
      await axios.delete(`/api/rewards-punishments/${id}`)
      // 如果删除后当前页没有数据，返回上一页
      if (rewards.value.length === 1 && page.value > 1) {
        page.value--
      }
      await fetchRewards()
    } catch (error) {
      console.error('Error deleting reward:', error)
    }
  }
}

onMounted(() => {
  fetchStudents()
  fetchRewards()
})
</script>

<template>
  <div>
    <div class="toolbar">
      <button @click="showForm = true; resetForm()" class="add-button-red">
        <span style="margin-right: 6px;">➕</span>添加记录
      </button>
      <div class="search-container">
        <input 
          v-model="searchKeyword" 
          type="text" 
          placeholder="🔍 搜索记录（学生姓名、学号、类型、标题、描述、日期）" 
          class="search-input"
        />
        <span v-if="searchKeyword" class="search-result">
          找到 {{ filteredRewards.length }} 条记录
        </span>
      </div>
    </div>
    
    <table v-if="filteredRewards.length">
      <thead>
        <tr>
          <th>学生姓名</th>
          <th>类型</th>
          <th>标题</th>
          <th>描述</th>
          <th>日期</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="rp in filteredRewards" :key="rp.id">
          <td>{{ rp.student_name }}</td>
          <td>{{ rp.type }}</td>
          <td>{{ rp.title }}</td>
          <td>{{ rp.description }}</td>
          <td>{{ rp.date }}</td>
          <td>
            <button @click="editReward(rp)">编辑</button>
            <button @click="deleteReward(rp.id)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="!searchKeyword">暂无记录</p>
    <p v-else>未找到匹配的记录</p>

    <div v-if="total > 0 && !searchKeyword" class="pagination">
      <button :disabled="page === 1" @click="changePage(page - 1)">上一页</button>
      <span>第 {{ page }} / {{ totalPages }} 页</span>
      <button :disabled="page === totalPages" @click="changePage(page + 1)">下一页</button>
    </div>

    <div v-if="showForm" class="modal">
      <div class="modal-content">
        <h2>{{ isEdit ? '编辑记录' : '添加记录' }}</h2>
        <form @submit.prevent="submitForm">
          <div class="form-group">
            <select v-model="currentReward.student_id" required>
              <option value="">选择学生</option>
              <option v-for="student in students" :key="student.student_id" :value="student.student_id">{{ student.name }}</option>
            </select>
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">学生: 选择一位学生</div>
            </div>
          </div>
          <div class="form-group">
            <select v-model="currentReward.type" required>
              <option value="">选择类型</option>
              <option value="奖励">奖励</option>
              <option value="处分">处分</option>
            </select>
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">类型: 奖励或处分</div>
            </div>
          </div>
          <div class="form-group">
            <input v-model="currentReward.title" placeholder="标题" required />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">标题: 记录标题</div>
            </div>
          </div>
          <div class="form-group">
            <input v-model="currentReward.description" placeholder="描述" />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">描述: 详细描述</div>
            </div>
          </div>
          <div class="form-group">
            <input v-model="currentReward.date" type="date" required />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">日期: 事件日期</div>
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
/* 红色主题 - 奖励处分 */
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
  background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
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
  background-color: #ffebee;
  transform: scale(1.001);
  box-shadow: 0 2px 8px rgba(244, 67, 54, 0.1);
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

td button:last-of-type {
  background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
  color: white;
}

/* 工具栏 */
.toolbar {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.add-button-red {
  background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  white-space: nowrap;
}

.add-button-red:hover {
  box-shadow: 0 4px 12px rgba(244, 67, 54, 0.4);
}

.search-container {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
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
  border-color: #f44336;
  box-shadow: 0 0 0 3px rgba(244, 67, 54, 0.1);
}

.search-result {
  color: #f44336;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
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
  background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
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
  border-color: #f44336;
  background: white;
  box-shadow: 0 0 0 3px rgba(244, 67, 54, 0.1);
}

.info-container {
  position: relative;
  margin-left: 10px;
}

.info-ellipsis {
  cursor: pointer;
  color: #f44336;
  font-weight: bold;
  font-size: 18px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #ffebee;
  transition: all 0.3s ease;
}

.info-ellipsis:hover {
  background: #f44336;
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
  background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
}

button[type="submit"]:hover {
  box-shadow: 0 4px 12px rgba(244, 67, 54, 0.4);
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
  background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
}

.pagination button:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(244, 67, 54, 0.4);
  transform: translateY(-2px);
}

.pagination button:disabled {
  background: #e0e0e0;
  color: #999;
  cursor: not-allowed;
  opacity: 0.6;
}

.pagination span {
  color: #f44336;
  font-weight: 500;
}
</style>

