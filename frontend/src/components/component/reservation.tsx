/**
 * 예약 컴포넌트 - FastAPI 백엔드와 연결
 * 이사 예약 생성 및 관리 기능 포함
 */
'use client';

import { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button"
import { AvatarImage, Avatar } from "@/components/ui/avatar"
import { Calendar } from "@/components/ui/calendar"
import { Checkbox } from "@/components/ui/checkbox"
import { Textarea } from "@/components/ui/textarea"
import { TableHead, TableRow, TableHeader, TableBody, Table, TableCell } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { JSX, SVGProps } from "react"
import { ReservationService } from '@/lib/services/reservations';
import type { CreateReservationRequest, Reservation } from '@/lib/services/reservations';

interface TimeSlot {
  id: string;
  label: string;
  startTime: string;
  endTime: string;
  isAvailable: boolean;
}

export function Reservation() {
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date());
  const [selectedTimeSlot, setSelectedTimeSlot] = useState<string>('');
  const [reservationType, setReservationType] = useState<'elevator' | 'parking' | 'other'>('elevator');
  const [description, setDescription] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [timeSlots] = useState<TimeSlot[]>([
    { id: '1', label: '9시~12시', startTime: '09:00', endTime: '12:00', isAvailable: true },
    { id: '2', label: '12시~15시', startTime: '12:00', endTime: '15:00', isAvailable: true },
    { id: '3', label: '15시~18시', startTime: '15:00', endTime: '18:00', isAvailable: true },
  ]);

  /**
   * 예약 타입 변경 처리
   */
  const handleReservationTypeChange = (type: 'elevator' | 'parking' | 'other', checked: boolean) => {
    if (checked) {
      setReservationType(type);
    }
  };

  /**
   * 시간대 선택 처리
   */
  const handleTimeSlotSelect = (timeSlotId: string) => {
    setSelectedTimeSlot(timeSlotId);
    setError(null);
  };

  /**
   * 예약 충돌 검사
   */
  const checkConflict = async (date: Date, timeSlot: TimeSlot) => {
    try {
      const startDateTime = new Date(date);
      const endDateTime = new Date(date);
      
      const [startHour] = timeSlot.startTime.split(':').map(Number);
      const [endHour] = timeSlot.endTime.split(':').map(Number);
      
      startDateTime.setHours(startHour, 0, 0, 0);
      endDateTime.setHours(endHour, 0, 0, 0);

      const result = await ReservationService.checkConflict(
        reservationType,
        startDateTime.toISOString(),
        endDateTime.toISOString()
      );

      return result.has_conflict;
    } catch (error) {
      console.error('충돌 검사 실패:', error);
      return false;
    }
  };

  /**
   * 예약 생성 처리
   */
  const handleSubmit = async () => {
    if (!selectedDate || !selectedTimeSlot) {
      setError('날짜와 시간대를 선택해주세요.');
      return;
    }

    const timeSlot = timeSlots.find(slot => slot.id === selectedTimeSlot);
    if (!timeSlot) {
      setError('유효하지 않은 시간대입니다.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // 충돌 검사
      const hasConflict = await checkConflict(selectedDate, timeSlot);
      if (hasConflict) {
        setError('선택한 시간대에 이미 예약이 있습니다. 다른 시간대를 선택해주세요.');
        setIsLoading(false);
        return;
      }

      // 예약 생성
      const startDateTime = new Date(selectedDate);
      const endDateTime = new Date(selectedDate);
      
      const [startHour] = timeSlot.startTime.split(':').map(Number);
      const [endHour] = timeSlot.endTime.split(':').map(Number);
      
      startDateTime.setHours(startHour, 0, 0, 0);
      endDateTime.setHours(endHour, 0, 0, 0);

      const reservationData: CreateReservationRequest = {
        reservation_type: reservationType,
        start_time: startDateTime.toISOString(),
        end_time: endDateTime.toISOString(),
        description: description.trim() || undefined,
      };

      const result = await ReservationService.createReservation(reservationData);
      
      setSuccess('예약이 성공적으로 생성되었습니다. 관리자 승인을 기다려주세요.');
      
      // 폼 초기화
      setSelectedDate(new Date());
      setSelectedTimeSlot('');
      setDescription('');
      
    } catch (error: any) {
      console.error('예약 생성 실패:', error);
      setError(error.message || '예약 생성에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between p-4">
      <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-blue-600">FNM - 이사 예약</h1>
      </div>
      </div>
      <div className="flex flex-col md:flex-row md:space-x-8">
        <div className="flex flex-col items-center">
          <div className="p-4">
            <Calendar 
              className="rounded-md border" 
              mode="single"
              selected={selectedDate}
              onSelect={setSelectedDate}
              disabled={(date) => date < new Date()}
            />
          </div>
          <div className="mt-4 p-4 w-full">
            <h3 className="text-lg font-semibold">이사 방식</h3>
            <div className="flex items-center space-x-2 my-2">
              <Checkbox 
                id="elevator-use"
                checked={reservationType === 'elevator'}
                onCheckedChange={(checked) => handleReservationTypeChange('elevator', checked as boolean)}
              />
              <label className="text-sm font-medium" htmlFor="elevator-use">
                엘리베이터 이용
              </label>
            </div>
            <div className="flex items-center space-x-2 my-2">
              <Checkbox 
                id="parking-use"
                checked={reservationType === 'parking'}
                onCheckedChange={(checked) => handleReservationTypeChange('parking', checked as boolean)}
              />
              <label className="text-sm font-medium" htmlFor="parking-use">
                주차장 이용
              </label>
            </div>
            <div className="flex items-center space-x-2 my-2">
              <Checkbox 
                id="other-use"
                checked={reservationType === 'other'}
                onCheckedChange={(checked) => handleReservationTypeChange('other', checked as boolean)}
              />
              <label className="text-sm font-medium" htmlFor="other-use">
                기타
              </label>
            </div>
            <Textarea 
              placeholder="요청사항을 입력해주세요"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="mt-2"
            />
            {/* 에러/성공 메시지 */}
            {error && (
              <div className="mt-2 p-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md">
                {error}
              </div>
            )}
            {success && (
              <div className="mt-2 p-2 text-sm text-green-600 bg-green-50 border border-green-200 rounded-md">
                {success}
              </div>
            )}
            <Button 
              className="mt-4 w-full"
              onClick={handleSubmit}
              disabled={isLoading || !selectedDate || !selectedTimeSlot}
            >
              {isLoading ? '예약 중...' : '예약하기'}
            </Button>
          </div>
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold mb-4">시간대 선택</h3>
          <Table>
            <TableHeader>
              <TableRow>
                {timeSlots.map((slot) => (
                  <TableHead key={slot.id} className="w-[150px] text-center">
                    {slot.label}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow>
                {timeSlots.map((slot) => (
                  <TableCell key={slot.id} className="text-center">
                    <Button
                      variant={selectedTimeSlot === slot.id ? "default" : "outline"}
                      size="sm"
                      onClick={() => handleTimeSlotSelect(slot.id)}
                      disabled={!slot.isAvailable}
                      className="w-full"
                    >
                      {slot.isAvailable ? '선택' : '불가'}
                    </Button>
                  </TableCell>
                ))}
              </TableRow>
            </TableBody>
          </Table>
          <p className="text-sm mt-4 text-gray-600">
            - 원하시는 이용을 위해 지정 시간 최소 3시간이라는 점 양해 부탁드립니다.
          </p>
          {selectedDate && (
            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
              <p className="text-sm">
                <strong>선택된 날짜:</strong> {selectedDate.toLocaleDateString('ko-KR')}
              </p>
              {selectedTimeSlot && (
                <p className="text-sm">
                  <strong>선택된 시간:</strong> {timeSlots.find(slot => slot.id === selectedTimeSlot)?.label}
                </p>
              )}
              <p className="text-sm">
                <strong>예약 유형:</strong> {
                  reservationType === 'elevator' ? '엘리베이터 이용' :
                  reservationType === 'parking' ? '주차장 이용' : '기타'
                }
              </p>
          </div>
          )}
        </div>
      </div>
    </div>
  )
}

function ChevronLeftIcon(props: JSX.IntrinsicAttributes & SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="m15 18-6-6 6-6" />
    </svg>
  )
}

function ChevronRightIcon(props: JSX.IntrinsicAttributes & SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="m9 18 6-6-6-6" />
    </svg>
  )
}
