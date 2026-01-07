<script setup>
import { ref, onMounted, nextTick, watch, computed } from 'vue'
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
const courses = ref([])
const studentCourses = ref([])
const showForm = ref(false)
const isEdit = ref(false)
const searchKeyword = ref('')
const currentStudentCourse = ref({
  student_id: '',
  course_id: '',
  exam_score: 0,
  daily_score: 0,
  semester: ''
})
const errorMessage = ref('')
const expandedRows = ref([])  // Track expanded rows
const attendanceData = ref({})  // Store attendance for each row
const highlightedRow = ref(null)  // Track highlighted row
const showTooltip = ref({})  // Track tooltip visibility
const page = ref(1)
const limit = 10
const total = ref(0)

const filteredStudentCourses = computed(() => {
  // 如果是只读模式，确保只显示当前学生的选课记录
  let filtered = studentCourses.value
  if (props.readonly && props.studentId) {
    filtered = filtered.filter(sc => {
      const studentId = sc.student_id || sc.studentId
      return studentId === props.studentId
    })
  }
  
  if (!searchKeyword.value.trim()) {
    return filtered
  }
  
  const keyword = searchKeyword.value.toLowerCase().trim()
  return filtered.filter(sc => {
    return (
      (sc.student_name && sc.student_name.toLowerCase().includes(keyword)) ||
      (sc.student_id && sc.student_id.toLowerCase().includes(keyword)) ||
      (sc.course_name && sc.course_name.toLowerCase().includes(keyword)) ||
      (sc.course_code && sc.course_code.toLowerCase().includes(keyword)) ||
      (sc.semester && sc.semester.toLowerCase().includes(keyword)) ||
      (sc.exam_score && String(sc.exam_score).includes(keyword)) ||
      (sc.daily_score && String(sc.daily_score).includes(keyword)) ||
      (sc.final_score && String(sc.final_score).includes(keyword))
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

const fetchCourses = async () => {
  try {
    // 获取所有课程（不分页，用于下拉选择）
    const response = await axios.get('/api/courses', {
      params: { page: 1, limit: 1000 }
    })
    courses.value = response.data.data || response.data || []
  } catch (error) {
    console.error('Error fetching courses:', error)
    courses.value = []
  }
}

const fetchStudentCourses = async () => {
  try {
    let response
    if (props.readonly && props.studentId) {
      // 学生角色：只获取自己的选课记录（不分页，获取所有）
      response = await axios.get('/api/student-courses', {
        params: { student_id: props.studentId, page: 1, limit: 1000 }
      })
    } else {
      // 管理员角色：获取所有选课记录（分页）
      response = await axios.get('/api/student-courses', {
        params: { page: page.value, limit }
      })
    }
    
    console.log('API Response:', response)  // Debug log
    console.log('Fetched student courses data:', response.data)  // Debug log
    console.log('Data type:', Array.isArray(response.data) ? 'Array' : typeof response.data)  // Debug log
    
    // 确保返回的是数组
    let data = []
    if (Array.isArray(response.data)) {
      data = response.data
      total.value = data.length
    } else if (response.data && Array.isArray(response.data.data)) {
      data = response.data.data
      total.value = response.data.total || 0
    }
    
    // 如果是只读模式，再次过滤确保只包含当前学生的数据
    if (props.readonly && props.studentId) {
      data = data.filter(sc => {
        const studentId = sc.student_id || sc.studentId
        return studentId === props.studentId
      })
      total.value = data.length
      console.log('Filtered for student view. studentId:', props.studentId, 'Records:', data.length)
    }
    
    // 使用 nextTick 确保响应式更新
    await nextTick()
    studentCourses.value = [...data]  // 创建新数组确保响应式
    
    console.log('studentCourses.value after assignment:', studentCourses.value)  // Debug log
    console.log('studentCourses.value length:', studentCourses.value.length)  // Debug log
    console.log('Is array?', Array.isArray(studentCourses.value))  // Debug log
  } catch (error) {
    console.error('Error fetching student courses:', error)
    console.error('Error details:', error.response)  // Debug log
    studentCourses.value = []
    total.value = 0
  }
}

// 监听 studentCourses 的变化
watch(studentCourses, (newVal) => {
  console.log('studentCourses changed:', newVal, 'length:', newVal?.length)
}, { deep: true, immediate: true })

const resetForm = () => {
  currentStudentCourse.value = {
    student_id: '',
    course_id: '',
    exam_score: 0,
    daily_score: 0,
    semester: ''
  }
  isEdit.value = false
  errorMessage.value = ''
}

const submitForm = async () => {
  // 如果是学生模式，确保使用当前学生的ID，且不能编辑成绩
  if (props.readonly && props.studentId) {
    if (isEdit.value) {
      // 学生不能编辑成绩
      alert('学生无权编辑成绩，请联系老师或管理员')
      return
    }
    // 添加选课时，强制使用当前学生的ID
    currentStudentCourse.value.student_id = props.studentId
    // 学生选课时，成绩应该为0或留空，由老师后续填写
    currentStudentCourse.value.exam_score = 0
    currentStudentCourse.value.daily_score = 0
  }
  
  // 确保数据类型正确
  currentStudentCourse.value.exam_score = parseFloat(currentStudentCourse.value.exam_score) || 0
  currentStudentCourse.value.daily_score = parseFloat(currentStudentCourse.value.daily_score) || 0
  
  // 转换 course_id 为整数（编辑时course_id应该已经存在，新增时需要验证）
  if (currentStudentCourse.value.course_id !== null && currentStudentCourse.value.course_id !== undefined && currentStudentCourse.value.course_id !== '') {
    const courseIdNum = parseInt(currentStudentCourse.value.course_id)
    currentStudentCourse.value.course_id = isNaN(courseIdNum) ? null : courseIdNum
  }
  
  // 新增时验证必需字段
  if (!isEdit.value) {
    if (!currentStudentCourse.value.student_id || !currentStudentCourse.value.course_id) {
      errorMessage.value = '请选择学生和课程'
      alert('请选择学生和课程')
      return
    }
  }
  if (!props.readonly && (currentStudentCourse.value.exam_score > 100 || currentStudentCourse.value.daily_score > 100)) {
    errorMessage.value = '成绩不能超过100分'
    alert('成绩不能超过100分')
    return
  }
  console.log('Submitting form data:', currentStudentCourse.value)  // Debug log
  try {
    if (isEdit.value) {
      await axios.put(`/api/student-courses/${currentStudentCourse.value.id}`, currentStudentCourse.value)
    } else {
      await axios.post('/api/student-courses', currentStudentCourse.value)
    }
    resetForm()
    showForm.value = false
    await fetchStudentCourses()  // Force refresh
  } catch (error) {
    console.error('Submit error:', error)  // Debug log
    console.error('Error response:', error.response)  // Debug log
    errorMessage.value = error.response?.data?.message || '添加失败，请检查网络或输入'
    alert(errorMessage.value)
  }
}

const editStudentCourse = (sc) => {
  if (props.readonly) {
    // 学生不能编辑成绩
    alert('学生无权编辑成绩，请联系老师或管理员')
    return
  }
  currentStudentCourse.value = { ...sc }
  isEdit.value = true
  showForm.value = true
}

const deleteStudentCourse = async (id) => {
  if (props.readonly) {
    // 学生不能删除选课
    alert('学生无权删除选课，请联系老师或管理员')
    return
  }
  if (confirm('确认删除?')) {
    try {
      await axios.delete(`/api/student-courses/${id}`)
      // 如果删除后当前页没有数据，返回上一页
      if (studentCourses.value.length === 1 && page.value > 1) {
        page.value--
      }
      await fetchStudentCourses()
    } catch (error) {
      console.error('Error deleting student course:', error)
    }
  }
}

const changePage = (newPage) => {
  page.value = newPage
  fetchStudentCourses()
}

const totalPages = computed(() => Math.ceil(total.value / limit))

const toggleExpand = async (id, student_id, course_id) => {
  const index = expandedRows.value.indexOf(id)
  if (index === -1) {
    expandedRows.value.push(id)
    if (!attendanceData.value[id]) {
      await fetchAttendanceForRow(id, student_id, course_id)
    }
  } else {
    expandedRows.value.splice(index, 1)
  }
}

const toggleAllCourses = () => {
  highlightedRow.value = 'all'
  toggleExpand('all', null, null)
}

const addAttendanceAll = () => {
  // Placeholder: Open add modal for all courses
  alert('添加所有课程考勤')
}

const deleteAttendance = async (id, studentId, courseId, rowId) => {
  if (confirm('确认删除?')) {
    try {
      await axios.delete(`/api/attendance/${id}`)
      // Refresh the specific row's attendance
      if (rowId) {
        await fetchAttendanceForRow(rowId, studentId, courseId)
      }
      // Also refresh all attendance if needed
      if (expandedRows.value.includes('all')) {
        await fetchAttendanceForRow('all', null, null)
      }
    } catch (error) {
      console.error('Error deleting attendance:', error)
    }
  }
}

const fetchAttendanceForRow = async (id, student_id, course_id) => {
  try {
    const params = { student_id, page: 1, limit: 10 }
    if (course_id) params.course_id = course_id
    const response = await axios.get('/api/attendance', { params })
    attendanceData.value[id] = response.data.data
  } catch (error) {
    console.error('Error fetching attendance:', error)
  }
}

const highlightRow = (id) => {
  highlightedRow.value = id
}

const editAttendance = (att) => {
  // TODO: Implement attendance editing modal or logic
  alert(`Editing attendance ID: ${att.id}`)  // Placeholder
}

const openAddForm = () => {
  console.log('Opening add form')
  resetForm()
  // 如果是学生模式，自动填充当前学生的ID
  if (props.readonly && props.studentId) {
    currentStudentCourse.value.student_id = props.studentId
  }
  showForm.value = true
  console.log('showForm.value:', showForm.value)
}

const closeForm = () => {
  console.log('Closing form')
  showForm.value = false
  resetForm()
  errorMessage.value = ''
}

const showButtonTooltip = (id) => {
  if (!expandedRows.value.includes(id)) {
    showTooltip.value[id] = true
  }
}

const hideButtonTooltip = (id) => {
  showTooltip.value[id] = false
}

onMounted(() => {
  console.log('Component mounted, fetching data...')
  if (!props.readonly) {
    fetchStudents()
    fetchCourses()
  } else {
    // 学生模式下也需要获取课程列表，以便选课
    fetchCourses()
  }
  fetchStudentCourses().then(() => {
    console.log('After fetchStudentCourses, studentCourses.value:', studentCourses.value)
  })
})
</script>

<template>
    <div>
    <div v-if="!readonly" class="toolbar">
      <button @click="openAddForm" class="add-button-orange">
        <span style="margin-right: 6px;">➕</span>添加选课
      </button>
      <div class="search-container">
        <input 
          v-model="searchKeyword" 
          type="text" 
          placeholder="🔍 搜索选课（学生姓名、学号、课程名称、学期、成绩）" 
          class="search-input"
        />
        <span v-if="searchKeyword" class="search-result">
          找到 {{ filteredStudentCourses.length }} 条记录
        </span>
      </div>
    </div>
    <div v-else class="readonly-header">
      <h3 class="section-title-orange">📖 我的课程与成绩</h3>
      <p v-if="!props.studentId" class="info-hint">提示：未找到对应的学生信息，请联系管理员</p>
      <div class="toolbar">
        <button @click="openAddForm" class="add-button-orange">添加选课</button>
        <div class="search-container">
          <input 
            v-model="searchKeyword" 
            type="text" 
            placeholder="🔍 搜索课程（课程名称、学期、成绩）" 
            class="search-input"
          />
        </div>
      </div>
    </div>
    
    <div v-if="filteredStudentCourses && filteredStudentCourses.length > 0">
      <table>
        <thead>
          <tr>
            <th></th>  <!-- Expand column -->
            <th v-if="!readonly">学生姓名</th>
            <th>课程名称</th>
            <th>考试成绩 (70%)</th>
            <th>平时成绩 (30%)</th>
            <th>总成绩</th>
            <th>学期</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="sc in filteredStudentCourses" :key="sc.id || sc.student_id + '-' + sc.course_id">
          <tr :class="{ 'highlighted': highlightedRow === sc.id }" @click.stop="highlightRow(sc.id)">
          <td>
            <div 
              class="expand-button-container"
              @mouseenter="showButtonTooltip(sc.id)"
              @mouseleave="hideButtonTooltip(sc.id)"
            >
              <button 
                @click.stop="toggleExpand(sc.id, sc.student_id, sc.course_id)"
                class="expand-button"
              >{{ expandedRows.includes(sc.id) ? '-' : '+' }}</button>
              <div v-if="!expandedRows.includes(sc.id) && showTooltip[sc.id]" class="custom-tooltip">
                该学生考勤信息
              </div>
            </div>
          </td>
          <td v-if="!readonly">{{ sc.student_name || sc.name || '未知' }}</td>
          <td>{{ sc.course_name || sc.course_code || '未知' }}</td>
          <td>{{ sc.exam_score ?? 0 }}</td>
          <td>{{ sc.daily_score ?? 0 }}</td>
          <td>{{ sc.final_score ?? 0 }}</td>
            <td>{{ sc.semester || '' }}</td>
            <td v-if="!readonly">
              <button @click.stop="editStudentCourse(sc)">编辑成绩</button>
              <button @click.stop="deleteStudentCourse(sc.id)">删除</button>
            </td>
            <td v-else style="color: #999;">仅查看</td>
        </tr>
        <tr v-if="expandedRows.includes(sc.id)" class="expanded-row">
          <td :colspan="readonly ? 7 : 8" class="expanded-cell">
            <div class="expanded-content">
              <h4 class="section-title-orange">📅 该学生考勤信息</h4>
              <table class="sub-table">
                <thead>
                  <tr>
                    <th>日期</th>
                    <th>状态</th>
                    <th>原因</th>
                    <th v-if="!readonly">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="att in attendanceData[sc.id]" :key="att.id">
                    <td>{{ att.date }}</td>
                    <td>{{ att.status }}</td>
                    <td>{{ att.reason || '' }}</td>
                    <td v-if="!readonly">
                      <button @click.stop="editAttendance(att)" style="margin: 2px; padding: 4px 8px; font-size: 12px;">编辑</button>
                      <button @click.stop="deleteAttendance(att.id, sc.student_id, sc.course_id, sc.id)" style="margin: 2px; padding: 4px 8px; font-size: 12px;">删除</button>
                    </td>
                  </tr>
                  <tr v-if="!attendanceData[sc.id] || attendanceData[sc.id].length === 0">
                    <td :colspan="readonly ? 3 : 4" class="empty-state">暂无考勤记录</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </td>
        </tr>
          </template>
        </tbody>
      </table>
    </div>
    <div v-else-if="readonly && !props.studentId">
      <p style="color: #999;">未找到您的学生信息，请联系管理员</p>
    </div>
    <div v-else-if="readonly && !searchKeyword">
      <p>暂无您的选课记录</p>
    </div>
    <div v-else-if="!searchKeyword">
      <p>暂无选课记录</p>
    </div>
    <div v-else>
      <p>未找到匹配的选课记录</p>
    </div>

    <div v-if="total > 0 && !searchKeyword && !readonly" class="pagination">
      <button :disabled="page === 1" @click="changePage(page - 1)">上一页</button>
      <span>第 {{ page }} / {{ totalPages }} 页</span>
      <button :disabled="page === totalPages" @click="changePage(page + 1)">下一页</button>
    </div>

    <Teleport to="body">
      <div v-if="showForm" class="modal" style="display: flex !important; z-index: 9999;" @click.self="closeForm">
      <div class="modal-content" @click.stop>
        <h2>{{ isEdit ? '编辑成绩' : '添加选课' }}</h2>
        <form @submit.prevent="submitForm">
          <div class="form-group" v-if="!readonly">
            <select v-model="currentStudentCourse.student_id" required :disabled="isEdit">
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
            <select v-model="currentStudentCourse.course_id" required>
              <option value="">选择课程</option>
              <option v-for="course in courses" :key="course.id" :value="course.id">{{ course.course_name }}</option>
            </select>
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">课程: 选择一门课程</div>
            </div>
          </div>
          <div class="form-group" v-if="!readonly || !isEdit">
            <input v-model="currentStudentCourse.exam_score" type="number" placeholder="考试成绩" :disabled="readonly && !isEdit" />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">{{ readonly ? '考试成绩: 由老师填写（不可修改）' : '考试成绩: 0-100 分' }}</div>
            </div>
          </div>
          <div class="form-group" v-if="!readonly || !isEdit">
            <input v-model="currentStudentCourse.daily_score" type="number" placeholder="平时成绩" :disabled="readonly && !isEdit" />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">{{ readonly ? '平时成绩: 由老师填写（不可修改）' : '平时成绩: 0-100 分' }}</div>
            </div>
          </div>
          <div class="form-group">
            <input v-model="currentStudentCourse.semester" placeholder="学期" />
            <div class="info-container">
              <span class="info-ellipsis">...</span>
              <div class="tooltip">学期: e.g., 2023-1</div>
            </div>
          </div>
          <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
          <div class="buttons">
            <button type="submit">保存</button>
            <button type="button" @click.stop="closeForm">取消</button>
          </div>
        </form>
      </div>
    </div>
    </Teleport>
  </div>
</template>
<style scoped>
/* 橙色主题 - 选课管理 */
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
  background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
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
  background-color: #fff3e0;
  transform: scale(1.001);
  box-shadow: 0 2px 8px rgba(255, 152, 0, 0.1);
}

tbody tr.highlighted {
  background-color: #ffe0b2;
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

.add-button-orange {
  background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  white-space: nowrap;
}

.add-button-orange:hover {
  box-shadow: 0 4px 12px rgba(255, 152, 0, 0.4);
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
  border-color: #ff9800;
  box-shadow: 0 0 0 3px rgba(255, 152, 0, 0.1);
}

.search-result {
  color: #ff9800;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
}

.section-title-orange {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 22px;
  font-weight: 600;
  background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* 展开行 */
.expanded-row {
  background: #fafafa;
}

.expanded-cell {
  padding: 0 !important;
  border: none !important;
}

.expanded-content {
  padding: 25px;
  background: linear-gradient(to bottom, #fafafa 0%, #ffffff 100%);
  border-radius: 12px;
  margin: 15px;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.03);
}

.section-title-orange {
  color: #ff9800;
  font-weight: 600;
  margin: 0 0 15px 0;
  font-size: 16px;
  padding-bottom: 10px;
  border-bottom: 2px solid #e0e0e0;
}

.empty-state {
  text-align: center;
  color: #999;
  padding: 20px;
  font-style: italic;
}

/* 子表格 */
.sub-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  margin: 15px 0;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.sub-table th {
  background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
  padding: 12px;
  font-size: 13px;
}

.sub-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 13px;
}

.sub-table tbody tr:hover {
  background-color: #fff3e0;
}

/* 展开按钮 */
.expand-button-container {
  position: relative;
  display: inline-block;
}

.expand-button {
  cursor: pointer;
  padding: 6px 12px;
  min-width: 32px;
  height: 32px;
  border: 2px solid #ff9800;
  background: linear-gradient(135deg, #fff3e0 0%, #ffffff 100%);
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  font-weight: 600;
  color: #ff9800;
  font-size: 16px;
}

.expand-button:hover {
  background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
  color: white;
  transform: scale(1.1);
  box-shadow: 0 4px 8px rgba(255, 152, 0, 0.3);
}

.custom-tooltip {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-bottom: 5px;
  padding: 6px 10px;
  background-color: rgba(0, 0, 0, 0.85);
  color: white;
  font-size: 12px;
  border-radius: 4px;
  white-space: nowrap;
  z-index: 10000;
  pointer-events: none;
  animation: tooltipFadeIn 0.1s ease-out;
}

.custom-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 5px solid transparent;
  border-top-color: rgba(0, 0, 0, 0.85);
}

@keyframes tooltipFadeIn {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
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
  background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
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
  border-color: #ff9800;
  background: white;
  box-shadow: 0 0 0 3px rgba(255, 152, 0, 0.1);
}

.info-container {
  position: relative;
  margin-left: 10px;
}

.info-ellipsis {
  cursor: pointer;
  color: #ff9800;
  font-weight: bold;
  font-size: 18px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #fff3e0;
  transition: all 0.3s ease;
}

.info-ellipsis:hover {
  background: #ff9800;
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
  background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
}

button[type="submit"]:hover {
  box-shadow: 0 4px 12px rgba(255, 152, 0, 0.4);
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

.info-hint {
  color: #ff9800;
  font-size: 14px;
  margin: 8px 0 0 0;
  padding: 10px;
  background: #fff3cd;
  border-radius: 6px;
  border-left: 4px solid #ff9800;
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
  background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
}

.pagination button:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(255, 152, 0, 0.4);
  transform: translateY(-2px);
}

.pagination button:disabled {
  background: #e0e0e0;
  color: #999;
  cursor: not-allowed;
  opacity: 0.6;
}

.pagination span {
  color: #ff9800;
  font-weight: 500;
}
</style>

